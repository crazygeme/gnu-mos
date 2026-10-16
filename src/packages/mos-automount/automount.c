#include <gio/gio.h>

#define MOUNT_ATTEMPTS 6
#define RETRY_SECONDS 2

typedef struct {
    GVolume *volume;
    unsigned attempts;
    gulong changed;
    gboolean observed_mount;
} Attempt;
static void attempt_free(Attempt *attempt)
{
    g_signal_handler_disconnect(attempt->volume, attempt->changed);
    g_object_unref(attempt->volume); g_free(attempt);
}
static void volume_changed(GVolume *volume, gpointer data)
{
    Attempt *attempt = data;
    GMount *mount = g_volume_get_mount(volume);
    if (mount) { attempt->observed_mount = TRUE; g_object_unref(mount); }
}
static gboolean mount_attempt(gpointer data);
static void mounted(GObject *source, GAsyncResult *result, gpointer data)
{
    Attempt *attempt = data;
    GError *error = NULL;
    if (g_volume_mount_finish(G_VOLUME(source), result, &error)) {
        attempt_free(attempt); return;
    }
    /* Teardown of a detached filesystem can overlap discovery of its replacement. */
    gboolean transient = g_error_matches(error, G_IO_ERROR, G_IO_ERROR_BUSY) ||
                         g_error_matches(error, G_IO_ERROR, G_IO_ERROR_NO_SPACE) ||
                         g_error_matches(error, G_IO_ERROR, G_IO_ERROR_FAILED);
    if (transient && attempt->attempts < MOUNT_ATTEMPTS &&
        !attempt->observed_mount && g_volume_can_mount(attempt->volume)) {
        g_error_free(error);
        g_timeout_add_seconds(RETRY_SECONDS, mount_attempt, attempt); return;
    }
    char *name = g_volume_get_name(G_VOLUME(source));
    g_warning("Automatic mount of %s: %s", name, error->message);
    g_free(name); g_error_free(error); attempt_free(attempt);
}
static gboolean mount_attempt(gpointer data)
{
    Attempt *attempt = data;
    if (attempt->observed_mount || !g_volume_can_mount(attempt->volume)) {
        attempt_free(attempt); return G_SOURCE_REMOVE;
    }
    attempt->attempts++;
    g_volume_mount(attempt->volume, G_MOUNT_MOUNT_NONE, NULL, NULL, mounted, attempt);
    return G_SOURCE_REMOVE;
}
static void added(GVolumeMonitor *monitor, GVolume *volume, gpointer data)
{
    (void)monitor; (void)data;
    char *device = g_volume_get_identifier(volume, G_VOLUME_IDENTIFIER_KIND_UNIX_DEVICE);
    if (device && g_str_has_prefix(device, "/dev/sd") &&
        g_volume_should_automount(volume) && g_volume_can_mount(volume)) {
        Attempt *attempt = g_new0(Attempt, 1);
        attempt->volume = g_object_ref(volume);
        attempt->changed = g_signal_connect(volume, "changed", G_CALLBACK(volume_changed), attempt);
        mount_attempt(attempt);
    }
    g_free(device);
}
static void acquired(GDBusConnection *connection, const char *name, gpointer data)
{
    (void)connection; (void)name; (void)data;
    GVolumeMonitor *monitor = g_volume_monitor_get();
    g_signal_connect(monitor, "volume-added", G_CALLBACK(added), NULL);
    GList *volumes = g_volume_monitor_get_volumes(monitor);
    for (GList *entry = volumes; entry; entry = entry->next) added(monitor, entry->data, NULL);
    g_list_free_full(volumes, g_object_unref);
}
static void lost(GDBusConnection *connection, const char *name, gpointer data)
{
    (void)connection; (void)name;
    g_main_loop_quit(data);
}
int main(void)
{
    GMainLoop *loop = g_main_loop_new(NULL, FALSE);
    g_bus_own_name(G_BUS_TYPE_SESSION, "org.mos.Automount", G_BUS_NAME_OWNER_FLAGS_NONE,
                   NULL, acquired, lost, loop, NULL);
    g_main_loop_run(loop);
    g_main_loop_unref(loop);
    return 0;
}
