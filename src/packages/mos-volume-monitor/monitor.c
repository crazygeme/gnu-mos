#include <gio/gio.h>
#include <gmodule.h>
#include "../mos-storage/protocol.h"

typedef struct _MosMonitor MosMonitor;
typedef struct _MosVolume MosVolume;
typedef struct _MosMount MosMount;
typedef struct _MosDrive MosDrive;
struct _MosDrive { GObject parent; GWeakRef volume; char *device; };
typedef GObjectClass MosDriveClass;
struct _MosVolume {
    GObject parent;
    GWeakRef monitor;
    char *id, *device, *label, *uuid, *type;
    MosDrive *drive;
    MosMount *mount; /* Borrowed from the monitor's mount list. */
    gboolean present;
};
typedef GObjectClass MosVolumeClass;
struct _MosMount { GObject parent; MosVolume *volume; char *path; };
typedef GObjectClass MosMountClass;
struct _MosMonitor {
    GNativeVolumeMonitor parent;
    GDBusProxy *proxy;
    GHashTable *volumes;
    GList *mounts;
    gulong changed, owner;
    gboolean refreshing;
};
typedef GNativeVolumeMonitorClass MosMonitorClass;
static void drive_interface(GDriveIface *iface);
static void volume_interface(GVolumeIface *iface);
static void mount_interface(GMountIface *iface);
G_DEFINE_DYNAMIC_TYPE_EXTENDED(MosDrive, mos_drive, G_TYPE_OBJECT, 0,
                        G_IMPLEMENT_INTERFACE_DYNAMIC(G_TYPE_DRIVE, drive_interface))
G_DEFINE_DYNAMIC_TYPE_EXTENDED(MosVolume, mos_volume, G_TYPE_OBJECT, 0,
                        G_IMPLEMENT_INTERFACE_DYNAMIC(G_TYPE_VOLUME, volume_interface))
G_DEFINE_DYNAMIC_TYPE_EXTENDED(MosMount, mos_mount, G_TYPE_OBJECT, 0,
                        G_IMPLEMENT_INTERFACE_DYNAMIC(G_TYPE_MOUNT, mount_interface))
G_DEFINE_DYNAMIC_TYPE(MosMonitor, mos_monitor, G_TYPE_NATIVE_VOLUME_MONITOR)
static GList *active_monitors;
static void refresh(MosMonitor *monitor);

static void mos_volume_finalize(GObject *object)
{
    MosVolume *v = (MosVolume *)object;
    g_weak_ref_clear(&v->monitor);
    g_clear_object(&v->drive);
    g_free(v->id); g_free(v->device); g_free(v->label); g_free(v->uuid); g_free(v->type);
    G_OBJECT_CLASS(mos_volume_parent_class)->finalize(object);
}
static void mos_volume_class_init(MosVolumeClass *klass) { klass->finalize = mos_volume_finalize; }
static void mos_volume_class_finalize(MosVolumeClass *klass) { (void)klass; }
static void mos_volume_init(MosVolume *v) { g_weak_ref_init(&v->monitor, NULL); }
static void mos_mount_finalize(GObject *object)
{
    MosMount *mount = (MosMount *)object;
    g_clear_object(&mount->volume); g_free(mount->path);
    G_OBJECT_CLASS(mos_mount_parent_class)->finalize(object);
}
static void mos_mount_class_init(MosMountClass *klass) { klass->finalize = mos_mount_finalize; }
static void mos_mount_class_finalize(MosMountClass *klass) { (void)klass; }
static void mos_mount_init(MosMount *mount) { (void)mount; }
static char *volume_name(GVolume *volume)
{
    MosVolume *v = (MosVolume *)volume;
    return *v->label ? g_strdup(v->label) : g_strdup_printf("USB %s", v->device + 5);
}
static char *volume_uuid(GVolume *volume)
{
    MosVolume *v = (MosVolume *)volume;
    return *v->uuid ? g_strdup(v->uuid) : NULL;
}
static GIcon *volume_icon(GVolume *volume) { (void)volume; return g_themed_icon_new_with_default_fallbacks("drive-removable-media-usb"); }
static GIcon *volume_symbolic_icon(GVolume *volume) { (void)volume; return g_themed_icon_new_with_default_fallbacks("drive-removable-media-symbolic"); }
static GDrive *volume_drive(GVolume *volume) { return G_DRIVE(g_object_ref(((MosVolume *)volume)->drive)); }
static GMount *volume_mount(GVolume *volume)
{
    MosVolume *v = (MosVolume *)volume;
    return v->mount ? G_MOUNT(g_object_ref(v->mount)) : NULL;
}
static gboolean volume_can_mount(GVolume *volume)
{
    MosVolume *v = (MosVolume *)volume;
    return v->present && !v->mount;
}
static gboolean volume_can_eject(GVolume *volume) { (void)volume; return FALSE; }
static gboolean volume_auto(GVolume *volume) { return ((MosVolume *)volume)->present; }
static char *volume_identifier(GVolume *volume, const char *kind)
{
    MosVolume *v = (MosVolume *)volume;
    if (!strcmp(kind, G_VOLUME_IDENTIFIER_KIND_CLASS)) return g_strdup("device");
    if (!strcmp(kind, G_VOLUME_IDENTIFIER_KIND_UNIX_DEVICE)) return g_strdup(v->device);
    if (!strcmp(kind, G_VOLUME_IDENTIFIER_KIND_UUID)) return volume_uuid(volume);
    if (!strcmp(kind, G_VOLUME_IDENTIFIER_KIND_LABEL)) return g_strdup(v->label);
    return NULL;
}
static char **volume_identifiers(GVolume *volume)
{
    (void)volume;
    char **result = g_new0(char *, 5);
    result[0] = g_strdup(G_VOLUME_IDENTIFIER_KIND_UNIX_DEVICE);
    result[1] = g_strdup(G_VOLUME_IDENTIFIER_KIND_UUID);
    result[2] = g_strdup(G_VOLUME_IDENTIFIER_KIND_LABEL);
    result[3] = g_strdup(G_VOLUME_IDENTIFIER_KIND_CLASS);
    return result;
}
static const char *volume_sort_key(GVolume *volume) { return ((MosVolume *)volume)->device; }
static GFile *volume_activation_root(GVolume *volume) { (void)volume; return NULL; }

static void operation_done(GObject *source, GAsyncResult *result, gpointer data)
{
    GTask *task = data;
    GError *error = NULL;
    GVariant *reply = g_dbus_proxy_call_finish(G_DBUS_PROXY(source), result, &error);
    MosMonitor *monitor = g_task_get_task_data(task);
    if (reply) {
        g_variant_unref(reply); refresh(monitor); g_task_return_boolean(task, TRUE);
    } else {
        /* Storage service failures retain their explanatory message. */
        g_dbus_error_strip_remote_error(error);
        g_task_return_error(task, error);
    }
    g_object_unref(task);
}
static void operation(GObject *source, MosVolume *volume, const char *method,
                      GCancellable *cancel, GAsyncReadyCallback callback, gpointer data)
{
    GTask *task = g_task_new(source, cancel, callback, data);
    MosMonitor *monitor = g_weak_ref_get(&volume->monitor);
    if (!monitor || !volume->present || !monitor->proxy) {
        g_task_return_new_error(task, G_IO_ERROR, G_IO_ERROR_NOT_FOUND, "USB volume is disconnected");
        g_clear_object(&monitor); g_object_unref(task); return;
    }
    g_task_set_task_data(task, monitor, g_object_unref);
    g_dbus_proxy_call(monitor->proxy, method, g_variant_new("(s)", volume->id),
        G_DBUS_CALL_FLAGS_NONE, STORAGE_TIMEOUT_MS, cancel, operation_done, task);
}
static void volume_mount_async(GVolume *volume, GMountMountFlags flags, GMountOperation *op,
                              GCancellable *cancel, GAsyncReadyCallback callback, gpointer data)
{
    (void)flags; (void)op;
    operation(G_OBJECT(volume), (MosVolume *)volume, "Mount", cancel, callback, data);
}
static gboolean volume_mount_finish(GVolume *volume, GAsyncResult *result, GError **error)
{
    g_return_val_if_fail(g_task_is_valid(result, volume), FALSE);
    return g_task_propagate_boolean(G_TASK(result), error);
}
static GFile *mount_root(GMount *mount) { return g_file_new_for_path(((MosMount *)mount)->path); }
static char *mount_name(GMount *mount) { return volume_name(G_VOLUME(((MosMount *)mount)->volume)); }
static char *mount_uuid(GMount *mount) { return volume_uuid(G_VOLUME(((MosMount *)mount)->volume)); }
static GIcon *mount_icon(GMount *mount) { return volume_icon(G_VOLUME(((MosMount *)mount)->volume)); }
static GIcon *mount_symbolic_icon(GMount *mount) { return volume_symbolic_icon(G_VOLUME(((MosMount *)mount)->volume)); }
static GVolume *mount_volume(GMount *mount) { return G_VOLUME(g_object_ref(((MosMount *)mount)->volume)); }
static GDrive *mount_drive(GMount *mount) { return volume_drive(G_VOLUME(((MosMount *)mount)->volume)); }
static gboolean mount_can_unmount(GMount *mount)
{
    MosMount *m = (MosMount *)mount;
    return m->volume->present && m->volume->mount == m;
}
static gboolean mount_can_eject(GMount *mount) { (void)mount; return FALSE; }
static const char *mount_sort_key(GMount *mount) { return ((MosMount *)mount)->path; }
static void mount_unmount_async(GMount *mount, GMountUnmountFlags flags, GCancellable *cancel,
                               GAsyncReadyCallback callback, gpointer data)
{
    (void)flags;
    operation(G_OBJECT(mount), ((MosMount *)mount)->volume, "Unmount", cancel, callback, data);
}
static void mount_unmount_operation(GMount *mount, GMountUnmountFlags flags, GMountOperation *op,
                                   GCancellable *cancel, GAsyncReadyCallback callback, gpointer data)
{
    (void)op; mount_unmount_async(mount, flags, cancel, callback, data);
}
static gboolean mount_unmount_finish(GMount *mount, GAsyncResult *result, GError **error)
{
    g_return_val_if_fail(g_task_is_valid(result, mount), FALSE);
    return g_task_propagate_boolean(G_TASK(result), error);
}
static void volume_interface(GVolumeIface *iface)
{
    iface->get_name = volume_name; iface->get_uuid = volume_uuid;
    iface->get_icon = volume_icon; iface->get_symbolic_icon = volume_symbolic_icon;
    iface->get_drive = volume_drive; iface->get_mount = volume_mount;
    iface->can_mount = volume_can_mount; iface->can_eject = volume_can_eject;
    iface->mount_fn = volume_mount_async; iface->mount_finish = volume_mount_finish;
    iface->get_identifier = volume_identifier; iface->enumerate_identifiers = volume_identifiers;
    iface->should_automount = volume_auto; iface->get_activation_root = volume_activation_root;
    iface->get_sort_key = volume_sort_key;
}
static void mount_interface(GMountIface *iface)
{
    iface->get_root = mount_root; iface->get_default_location = mount_root;
    iface->get_name = mount_name; iface->get_uuid = mount_uuid;
    iface->get_icon = mount_icon; iface->get_symbolic_icon = mount_symbolic_icon;
    iface->get_volume = mount_volume; iface->get_drive = mount_drive;
    iface->can_unmount = mount_can_unmount; iface->can_eject = mount_can_eject;
    iface->unmount = mount_unmount_async; iface->unmount_finish = mount_unmount_finish;
    iface->unmount_with_operation = mount_unmount_operation;
    iface->unmount_with_operation_finish = mount_unmount_finish;
    iface->get_sort_key = mount_sort_key;
}
static void mos_drive_finalize(GObject *object)
{
    MosDrive *drive = (MosDrive *)object;
    g_weak_ref_clear(&drive->volume); g_free(drive->device);
    G_OBJECT_CLASS(mos_drive_parent_class)->finalize(object);
}
static void mos_drive_class_init(MosDriveClass *klass) { klass->finalize = mos_drive_finalize; }
static void mos_drive_class_finalize(MosDriveClass *klass) { (void)klass; }
static void mos_drive_init(MosDrive *drive) { g_weak_ref_init(&drive->volume, NULL); }
static char *drive_name(GDrive *drive) { (void)drive; return g_strdup("USB storage"); }
static GIcon *drive_icon(GDrive *drive) { (void)drive; return volume_icon(NULL); }
static GIcon *drive_symbolic_icon(GDrive *drive) { (void)drive; return volume_symbolic_icon(NULL); }
static gboolean drive_true(GDrive *drive) { (void)drive; return TRUE; }
static gboolean drive_false(GDrive *drive) { (void)drive; return FALSE; }
static GList *drive_volumes(GDrive *drive)
{
    MosVolume *v = g_weak_ref_get(&((MosDrive *)drive)->volume);
    if (v && v->present) return g_list_append(NULL, v);
    g_clear_object(&v); return NULL;
}
static gboolean drive_has_volumes(GDrive *drive)
{
    GList *list = drive_volumes(drive);
    gboolean present = list != NULL;
    g_list_free_full(list, g_object_unref); return present;
}
static char *drive_identifier(GDrive *drive, const char *kind)
{
    return !strcmp(kind, G_DRIVE_IDENTIFIER_KIND_UNIX_DEVICE) ? g_strdup(((MosDrive *)drive)->device) : NULL;
}
static char **drive_identifiers(GDrive *drive)
{
    (void)drive;
    char **result = g_new0(char *, 2);
    result[0] = g_strdup(G_DRIVE_IDENTIFIER_KIND_UNIX_DEVICE); return result;
}
static const char *drive_sort_key(GDrive *drive) { return ((MosDrive *)drive)->device; }
static GDriveStartStopType drive_start_stop(GDrive *drive) { (void)drive; return G_DRIVE_START_STOP_TYPE_UNKNOWN; }
static void drive_interface(GDriveIface *iface)
{
    iface->get_name = drive_name; iface->get_icon = drive_icon;
    iface->get_symbolic_icon = drive_symbolic_icon;
    iface->has_volumes = drive_has_volumes; iface->get_volumes = drive_volumes;
    iface->is_removable = drive_true; iface->is_media_removable = drive_true;
    iface->has_media = drive_has_volumes; iface->is_media_check_automatic = drive_true;
    iface->can_eject = drive_false; iface->can_poll_for_media = drive_false;
    iface->can_start = drive_false; iface->can_start_degraded = drive_false; iface->can_stop = drive_false;
    iface->get_identifier = drive_identifier; iface->enumerate_identifiers = drive_identifiers;
    iface->get_sort_key = drive_sort_key; iface->get_start_stop_type = drive_start_stop;
}
static void remove_mount(MosMonitor *monitor, MosVolume *v)
{
    MosMount *mount = v->mount;
    if (!mount) return;
    v->mount = NULL;
    monitor->mounts = g_list_remove(monitor->mounts, mount);
    g_signal_emit_by_name(mount, "unmounted");
    g_signal_emit_by_name(monitor, "mount-removed", mount);
    g_object_unref(mount);
}
static void refresh(MosMonitor *monitor)
{
    if (monitor->refreshing || !monitor->proxy) return;
    monitor->refreshing = TRUE;
    GError *error = NULL;
    GVariant *reply = g_dbus_proxy_call_sync(monitor->proxy, "List", NULL,
        G_DBUS_CALL_FLAGS_NONE, STORAGE_TIMEOUT_MS, NULL, &error);
    char *owner = g_dbus_proxy_get_name_owner(monitor->proxy);
    gboolean connected = owner != NULL;
    g_free(owner);
    if (!reply && connected) {
        g_warning("USB volume enumeration: %s", error->message);
        g_clear_error(&error); monitor->refreshing = FALSE; return;
    }
    g_clear_error(&error);
    GHashTable *seen = g_hash_table_new_full(g_str_hash, g_str_equal, g_free, NULL);
    if (reply) {
        GVariantIter *iter;
        const char *id, *device, *label, *uuid, *type, *path;
        g_variant_get(reply, "(a(ssssss))", &iter);
        while (g_variant_iter_loop(iter, "(&s&s&s&s&s&s)", &id, &device, &label, &uuid, &type, &path)) {
            g_hash_table_add(seen, g_strdup(id));
            MosVolume *v = g_hash_table_lookup(monitor->volumes, id);
            gboolean added = !v;
            if (!v) {
                v = g_object_new(mos_volume_get_type(), NULL);
                v->id = g_strdup(id); v->device = g_strdup(device); v->label = g_strdup(label);
                v->uuid = g_strdup(uuid); v->type = g_strdup(type); v->present = TRUE;
                v->drive = g_object_new(mos_drive_get_type(), NULL);
                v->drive->device = g_strdup(device);
                g_weak_ref_set(&v->drive->volume, v);
                g_weak_ref_set(&v->monitor, monitor);
                g_hash_table_insert(monitor->volumes, g_strdup(id), v);
            }
            gboolean mount_changed = (!v->mount && *path) ||
                (v->mount && strcmp(v->mount->path, path));
            if (mount_changed) {
                remove_mount(monitor, v);
                if (*path) {
                    MosMount *mount = g_object_new(mos_mount_get_type(), NULL);
                    mount->volume = g_object_ref(v); mount->path = g_strdup(path);
                    monitor->mounts = g_list_append(monitor->mounts, mount); v->mount = mount;
                }
            }
            if (added) {
                g_signal_emit_by_name(monitor, "drive-connected", v->drive);
                g_signal_emit_by_name(monitor, "volume-added", v);
            }
            if (mount_changed) {
                if (v->mount) g_signal_emit_by_name(monitor, "mount-added", v->mount);
                g_signal_emit_by_name(v, "changed");
                g_signal_emit_by_name(monitor, "volume-changed", v);
            }
        }
        g_variant_iter_free(iter); g_variant_unref(reply);
    }
    GHashTableIter iter; gpointer key, value;
    g_hash_table_iter_init(&iter, monitor->volumes);
    while (g_hash_table_iter_next(&iter, &key, &value)) {
        if (g_hash_table_contains(seen, key)) continue;
        MosVolume *v = value;
        v->present = FALSE; remove_mount(monitor, v);
        g_signal_emit_by_name(v, "removed");
        g_signal_emit_by_name(monitor, "volume-removed", v);
        g_signal_emit_by_name(v->drive, "disconnected");
        g_signal_emit_by_name(monitor, "drive-disconnected", v->drive);
        g_hash_table_iter_remove(&iter);
    }
    g_hash_table_unref(seen); monitor->refreshing = FALSE;
}
static void service_signal(GDBusProxy *proxy, const char *sender, const char *signal,
                           GVariant *parameters, gpointer data)
{
    (void)proxy; (void)sender; (void)parameters;
    if (!strcmp(signal, "Changed")) refresh(data);
}
static void service_owner(GObject *proxy, GParamSpec *spec, gpointer data)
{
    (void)proxy; (void)spec; refresh(data);
}
static GList *monitor_drives(GVolumeMonitor *monitor)
{
    GList *list = NULL;
    GHashTableIter iter; gpointer value;
    g_hash_table_iter_init(&iter, ((MosMonitor *)monitor)->volumes);
    while (g_hash_table_iter_next(&iter, NULL, &value))
        list = g_list_prepend(list, g_object_ref(((MosVolume *)value)->drive));
    return list;
}
static GList *monitor_volumes(GVolumeMonitor *monitor)
{
    GList *list = g_hash_table_get_values(((MosMonitor *)monitor)->volumes);
    for (GList *entry = list; entry; entry = entry->next) g_object_ref(entry->data);
    return list;
}
static GList *monitor_mounts(GVolumeMonitor *monitor)
{
    GList *list = g_list_copy(((MosMonitor *)monitor)->mounts);
    for (GList *entry = list; entry; entry = entry->next) g_object_ref(entry->data);
    return list;
}
static GVolume *monitor_volume_uuid(GVolumeMonitor *monitor, const char *uuid)
{
    GHashTableIter iter; gpointer value;
    g_hash_table_iter_init(&iter, ((MosMonitor *)monitor)->volumes);
    while (g_hash_table_iter_next(&iter, NULL, &value)) {
        MosVolume *v = value;
        if (!strcmp(v->uuid, uuid)) return G_VOLUME(g_object_ref(v));
    }
    return NULL;
}
static GMount *monitor_mount_uuid(GVolumeMonitor *monitor, const char *uuid)
{
    GVolume *volume = monitor_volume_uuid(monitor, uuid);
    GMount *mount = volume ? g_volume_get_mount(volume) : NULL;
    g_clear_object(&volume); return mount;
}
static GMount *mount_for_path(const char *path, GCancellable *cancel)
{
    (void)cancel;
    for (GList *m = active_monitors; m; m = m->next)
        for (GList *entry = ((MosMonitor *)m->data)->mounts; entry; entry = entry->next) {
            MosMount *mount = entry->data;
            if (!strcmp(mount->path, path)) return G_MOUNT(g_object_ref(mount));
        }
    return NULL;
}
static gboolean monitor_supported(void) { return TRUE; }
static void mos_monitor_finalize(GObject *object)
{
    MosMonitor *monitor = (MosMonitor *)object;
    active_monitors = g_list_remove(active_monitors, monitor);
    if (monitor->proxy) {
        g_signal_handler_disconnect(monitor->proxy, monitor->changed);
        g_signal_handler_disconnect(monitor->proxy, monitor->owner);
        g_clear_object(&monitor->proxy);
    }
    GHashTableIter iter; gpointer value;
    g_hash_table_iter_init(&iter, monitor->volumes);
    while (g_hash_table_iter_next(&iter, NULL, &value)) {
        MosVolume *v = value; v->mount = NULL; v->present = FALSE;
    }
    g_list_free_full(monitor->mounts, g_object_unref);
    g_hash_table_unref(monitor->volumes);
    G_OBJECT_CLASS(mos_monitor_parent_class)->finalize(object);
}
static void mos_monitor_class_init(MosMonitorClass *klass)
{
    G_OBJECT_CLASS(klass)->finalize = mos_monitor_finalize;
    GVolumeMonitorClass *vm = G_VOLUME_MONITOR_CLASS(klass);
    vm->is_supported = monitor_supported; vm->get_connected_drives = monitor_drives;
    vm->get_volumes = monitor_volumes; vm->get_mounts = monitor_mounts;
    vm->get_volume_for_uuid = monitor_volume_uuid; vm->get_mount_for_uuid = monitor_mount_uuid;
    klass->get_mount_for_mount_path = mount_for_path;
}
static void mos_monitor_class_finalize(MosMonitorClass *klass) { (void)klass; }
static void mos_monitor_init(MosMonitor *monitor)
{
    monitor->volumes = g_hash_table_new_full(g_str_hash, g_str_equal, g_free, g_object_unref);
    active_monitors = g_list_prepend(active_monitors, monitor);
    GError *error = NULL;
    monitor->proxy = g_dbus_proxy_new_for_bus_sync(G_BUS_TYPE_SYSTEM,
        G_DBUS_PROXY_FLAGS_DO_NOT_LOAD_PROPERTIES, NULL, STORAGE_BUS, STORAGE_PATH,
        STORAGE_INTERFACE, NULL, &error);
    if (!monitor->proxy) {
        g_warning("Storage bus connection: %s", error->message); g_error_free(error); return;
    }
    monitor->changed = g_signal_connect(monitor->proxy, "g-signal", G_CALLBACK(service_signal), monitor);
    monitor->owner = g_signal_connect(monitor->proxy, "notify::g-name-owner", G_CALLBACK(service_owner), monitor);
    refresh(monitor);
}
G_MODULE_EXPORT void g_io_module_load(GIOModule *module)
{
    mos_drive_register_type(G_TYPE_MODULE(module));
    mos_volume_register_type(G_TYPE_MODULE(module));
    mos_mount_register_type(G_TYPE_MODULE(module));
    mos_monitor_register_type(G_TYPE_MODULE(module));
    g_io_extension_point_implement(G_NATIVE_VOLUME_MONITOR_EXTENSION_POINT_NAME,
                                   mos_monitor_get_type(), "mos", 20);
}
G_MODULE_EXPORT void g_io_module_unload(GIOModule *module) { (void)module; }
G_MODULE_EXPORT char **g_io_module_query(void)
{
    char **points = g_new0(char *, 2);
    points[0] = g_strdup(G_NATIVE_VOLUME_MONITOR_EXTENSION_POINT_NAME);
    return points;
}
