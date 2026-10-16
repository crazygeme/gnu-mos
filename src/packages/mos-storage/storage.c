#define _GNU_SOURCE
#include <gio/gio.h>
#include <polkit/polkit.h>
#include <blkid/blkid.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <fcntl.h>
#include <mntent.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <stdio.h>
#include "protocol.h"

/* Device identities contain the attachment generation and the kernel dev_t. */
typedef struct {
    char *id, *device, *label, *uuid, *type, *mountpoint, *sysfs;
    dev_t dev;
    gboolean present;
} Volume;
static GHashTable *volumes;
static GDBusConnection *bus;
static PolkitAuthority *authority;
static const char introspection[] =
    "<node><interface name='" STORAGE_INTERFACE "'>"
    "<method name='List'><arg direction='out' type='a(ssssss)'/></method>"
    "<method name='Mount'><arg direction='in' type='s'/><arg direction='out' type='s'/></method>"
    "<method name='Unmount'><arg direction='in' type='s'/></method>"
    "<signal name='Changed'/></interface></node>";

static void changed(void)
{
    g_dbus_connection_emit_signal(bus, NULL, STORAGE_PATH, STORAGE_INTERFACE,
                                  "Changed", NULL, NULL);
}
static char *attribute(const char *directory, const char *name)
{
    char *path = g_build_filename(directory, name, NULL), *text = NULL;
    g_file_get_contents(path, &text, NULL, NULL);
    g_free(path);
    return text ? g_strstrip(text) : g_strdup("");
}
static gboolean current(Volume *v)
{
    char *generation = attribute(v->sysfs, "mos_generation");
    char *dev = attribute(v->sysfs, "dev");
    char *id = g_strdup_printf("%s:%s", generation, dev);
    struct stat st;
    gboolean result = !strcmp(id, v->id) && !stat(v->device, &st) &&
                      S_ISBLK(st.st_mode) && st.st_rdev == v->dev;
    g_free(generation); g_free(dev); g_free(id);
    return result;
}
static void volume_free(gpointer data)
{
    Volume *v = data;
    g_free(v->id); g_free(v->device); g_free(v->label); g_free(v->uuid);
    g_free(v->type); g_free(v->mountpoint); g_free(v->sysfs); g_free(v);
}
static char *probe_value(blkid_probe probe, const char *key)
{
    const char *value;
    size_t length;
    return !blkid_probe_lookup_value(probe, key, &value, &length) ?
        g_strndup(value, length) : g_strdup("");
}
static gboolean supported(const char *type)
{
    return !strcmp(type, "ext3") || !strcmp(type, "ext4");
}
static char *mounted_at(const char *device)
{
    FILE *file = setmntent("/proc/mounts", "r");
    struct mntent *entry;
    char *path = g_strdup("");
    if (!file) return path;
    while ((entry = getmntent(file))) {
        if (!strcmp(entry->mnt_fsname, device)) {
            g_free(path); path = g_strdup(entry->mnt_dir); break;
        }
    }
    endmntent(file);
    return path;
}
static Volume *probe_volume(const char *sysfs, const char *name, const char *id, dev_t dev)
{
    char *device = g_build_filename("/dev", name, NULL);
    int fd = open(device, O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    struct stat st;
    blkid_probe probe = NULL;
    Volume *v = NULL;
    if (fd < 0 || fstat(fd, &st) || !S_ISBLK(st.st_mode) || st.st_rdev != dev)
        goto out;
    probe = blkid_new_probe();
    if (!probe || blkid_probe_set_device(probe, fd, 0, 0)) goto out;
    blkid_probe_enable_partitions(probe, 0);
    blkid_probe_set_superblocks_flags(probe, BLKID_SUBLKS_LABEL | BLKID_SUBLKS_UUID | BLKID_SUBLKS_TYPE);
    if (blkid_do_safeprobe(probe)) goto out;
    char *type = probe_value(probe, "TYPE");
    if (!supported(type)) { g_free(type); goto out; }
    v = g_new0(Volume, 1);
    v->id = g_strdup(id); v->device = g_strdup(device);
    v->sysfs = g_strdup(sysfs); v->dev = dev; v->type = type;
    v->label = probe_value(probe, "LABEL"); v->uuid = probe_value(probe, "UUID");
    if (!g_utf8_validate(v->label, -1, NULL)) { g_free(v->label); v->label = g_strdup(name); }
    v->mountpoint = mounted_at(device);
    if (!current(v)) { volume_free(v); v = NULL; }
out:
    if (probe) blkid_free_probe(probe);
    if (fd >= 0) close(fd);
    g_free(device);
    return v;
}
static gboolean scan(gpointer unused)
{
    (void)unused;
    GHashTableIter iter;
    gpointer value;
    gboolean dirty = FALSE;
    /* Retire detached mounts before a new attachment can reuse its dev_t. */
    g_hash_table_iter_init(&iter, volumes);
    while (g_hash_table_iter_next(&iter, NULL, &value)) {
        Volume *v = value;
        if (current(v)) continue;
        if (*v->mountpoint && g_str_has_prefix(v->mountpoint, STORAGE_MEDIA_ROOT "/")) {
            if (umount2(v->mountpoint, MNT_DETACH) && errno != EINVAL && errno != ENOENT) {
                g_warning("Cannot retire %s: %s", v->mountpoint, g_strerror(errno));
                continue;
            }
            rmdir(v->mountpoint);
        }
        g_hash_table_iter_remove(&iter); dirty = TRUE;
    }
    GDir *directory = g_dir_open("/sys/class/block", 0, NULL);
    const char *name;
    while (directory && (name = g_dir_read_name(directory))) {
        char *sysfs = g_build_filename("/sys/class/block", name, NULL);
        char *generation = attribute(sysfs, "mos_generation");
        char *dev = attribute(sysfs, "dev");
        unsigned major_number, minor_number;
        char *id = g_strdup_printf("%s:%s", generation, dev);
        if (*generation && sscanf(dev, "%u:%u", &major_number, &minor_number) == 2 &&
            !g_hash_table_contains(volumes, id)) {
            Volume *v = probe_volume(sysfs, name, id, makedev(major_number, minor_number));
            if (v) { g_hash_table_insert(volumes, g_strdup(id), v); dirty = TRUE; }
        }
        g_free(sysfs); g_free(generation); g_free(dev); g_free(id);
    }
    if (directory) g_dir_close(directory);
    /* Reflect mounts changed by administrative commands. */
    g_hash_table_iter_init(&iter, volumes);
    while (g_hash_table_iter_next(&iter, NULL, &value)) {
        Volume *v = value;
        char *path = mounted_at(v->device);
        if (strcmp(path, v->mountpoint)) {
            g_free(v->mountpoint); v->mountpoint = path; dirty = TRUE;
        } else g_free(path);
    }
    if (dirty) changed();
    return G_SOURCE_CONTINUE;
}
static gboolean authorize(GDBusMethodInvocation *invocation, const char *action, uid_t *uid)
{
    GError *error = NULL;
    const char *sender = g_dbus_method_invocation_get_sender(invocation);
    GVariant *reply = g_dbus_connection_call_sync(bus, "org.freedesktop.DBus",
        "/org/freedesktop/DBus", "org.freedesktop.DBus", "GetConnectionUnixUser",
        g_variant_new("(s)", sender), G_VARIANT_TYPE("(u)"), 0, STORAGE_TIMEOUT_MS, NULL, &error);
    if (!reply) goto denied;
    guint32 number;
    g_variant_get(reply, "(u)", &number); g_variant_unref(reply); *uid = number;
    if (!number) return TRUE;
    PolkitSubject *subject = polkit_system_bus_name_new(sender);
    PolkitAuthorizationResult *result = polkit_authority_check_authorization_sync(
        authority, subject, action, NULL, POLKIT_CHECK_AUTHORIZATION_FLAGS_NONE, NULL, &error);
    g_object_unref(subject);
    gboolean allowed = result && polkit_authorization_result_get_is_authorized(result);
    g_clear_object(&result);
    if (allowed) return TRUE;
denied:
    g_dbus_method_invocation_return_error(invocation, G_IO_ERROR, G_IO_ERROR_PERMISSION_DENIED,
                                         "Storage authorization denied%s%s", error ? ": " : "", error ? error->message : "");
    g_clear_error(&error);
    return FALSE;
}
static void method_call(GDBusConnection *connection, const char *sender, const char *path,
    const char *interface, const char *method, GVariant *parameters,
    GDBusMethodInvocation *invocation, gpointer data)
{
    (void)connection; (void)sender; (void)path; (void)interface; (void)data;
    scan(NULL);
    if (!strcmp(method, "List")) {
        GVariantBuilder result;
        g_variant_builder_init(&result, G_VARIANT_TYPE("a(ssssss)"));
        GHashTableIter iter; gpointer value;
        g_hash_table_iter_init(&iter, volumes);
        while (g_hash_table_iter_next(&iter, NULL, &value)) {
            Volume *v = value;
            g_variant_builder_add(&result, "(ssssss)", v->id, v->device, v->label,
                                  v->uuid, v->type, v->mountpoint);
        }
        g_dbus_method_invocation_return_value(invocation, g_variant_new("(a(ssssss))", &result));
        return;
    }
    uid_t uid;
    gboolean mounting = !strcmp(method, "Mount");
    if (!authorize(invocation, mounting ? "org.mos.storage.mount" : "org.mos.storage.unmount", &uid)) return;
    const char *id;
    g_variant_get(parameters, "(&s)", &id);
    Volume *v = g_hash_table_lookup(volumes, id);
    if (!v || !current(v)) {
        g_dbus_method_invocation_return_error(invocation, G_IO_ERROR, G_IO_ERROR_NOT_FOUND, "USB volume is disconnected"); return;
    }
    if (mounting) {
        if (!*v->mountpoint) {
            char *digest = g_compute_checksum_for_string(G_CHECKSUM_SHA256, v->id, -1);
            char *target = g_strdup_printf(STORAGE_MEDIA_ROOT "/%s-%.12s", strrchr(v->device, '/') + 1, digest);
            g_free(digest);
            struct stat st;
            if (mkdir(target, 0755) && errno != EEXIST) { g_free(target); goto failure; }
            if (lstat(target, &st) || !S_ISDIR(st.st_mode) || st.st_uid || (st.st_mode & 0022)) {
                g_free(target); errno = EPERM; goto failure;
            }
            if (mount(v->device, target, v->type, MS_NOSUID | MS_NODEV, NULL)) {
                int saved = errno; rmdir(target); g_free(target); errno = saved; goto failure;
            }
            if (!current(v)) { umount2(target, MNT_DETACH); rmdir(target); g_free(target); errno = ENODEV; goto failure; }
            g_free(v->mountpoint); v->mountpoint = target;
            changed();
        }
        g_dbus_method_invocation_return_value(invocation, g_variant_new("(s)", v->mountpoint));
    } else {
        if (*v->mountpoint) {
            if (!g_str_has_prefix(v->mountpoint, STORAGE_MEDIA_ROOT "/")) { errno = EPERM; goto failure; }
            /* MOS provides global filesystem synchronization. */
            sync();
            if (umount2(v->mountpoint, 0)) goto failure;
            rmdir(v->mountpoint); g_free(v->mountpoint); v->mountpoint = g_strdup(""); changed();
        }
        g_dbus_method_invocation_return_value(invocation, NULL);
    }
    return;
failure:
    g_dbus_method_invocation_return_error(invocation, G_IO_ERROR, g_io_error_from_errno(errno), "%s", g_strerror(errno));
}
static void acquired(GDBusConnection *connection, const char *name, gpointer data)
{
    (void)name; (void)data;
    bus = connection;
    GError *error = NULL;
    GDBusNodeInfo *info = g_dbus_node_info_new_for_xml(introspection, &error);
    static const GDBusInterfaceVTable vtable = { .method_call = method_call };
    if (!info || !g_dbus_connection_register_object(bus, STORAGE_PATH, info->interfaces[0], &vtable, NULL, NULL, &error))
        g_error("Storage service registration: %s", error->message);
    g_dbus_node_info_unref(info);
    scan(NULL); g_timeout_add_seconds(1, scan, NULL);
}
static void lost(GDBusConnection *connection, const char *name, gpointer data)
{
    (void)connection; (void)name; (void)data;
    g_error("Storage service bus name unavailable");
}
int main(void)
{
    if (geteuid()) return 1;
    umask(022);
    g_setenv("GIO_USE_VFS", "local", TRUE);
    if (g_mkdir_with_parents(STORAGE_MEDIA_ROOT, 0755)) return 1;
    struct stat st;
    if (lstat(STORAGE_MEDIA_ROOT, &st) || !S_ISDIR(st.st_mode) || st.st_uid || (st.st_mode & 0022)) return 1;
    GError *error = NULL;
    authority = polkit_authority_get_sync(NULL, &error);
    if (!authority) g_error("Storage authority: %s", error->message);
    volumes = g_hash_table_new_full(g_str_hash, g_str_equal, g_free, volume_free);
    g_bus_own_name(G_BUS_TYPE_SYSTEM, STORAGE_BUS, G_BUS_NAME_OWNER_FLAGS_NONE, acquired, NULL, lost, NULL, NULL);
    g_main_loop_run(g_main_loop_new(NULL, FALSE));
    return 0;
}
