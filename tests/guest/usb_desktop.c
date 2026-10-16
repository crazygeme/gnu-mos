/* Execute within the graphical session as an unprivileged desktop account. */
#include <gio/gio.h>
#include <stdio.h>
#include <string.h>

static gboolean complete, succeeded;
static GError *operation_error;
static void mount_done(GObject *source, GAsyncResult *result, gpointer data)
{
    (void)data;
    succeeded = g_volume_mount_finish(G_VOLUME(source), result, &operation_error);
    complete = TRUE;
}
static void unmount_done(GObject *source, GAsyncResult *result, gpointer data)
{
    (void)data;
    succeeded = g_mount_unmount_with_operation_finish(G_MOUNT(source), result, &operation_error);
    complete = TRUE;
}
static void wait_operation(void)
{
    while (!complete) g_main_context_iteration(NULL, TRUE);
    if (!succeeded) g_error("Volume operation failed: %s", operation_error->message);
    complete = FALSE;
}
static gboolean stop_wait(gpointer data) { *(gboolean *)data = TRUE; return G_SOURCE_REMOVE; }
static void settle(unsigned seconds)
{
    gboolean elapsed = FALSE;
    g_timeout_add_seconds(seconds, stop_wait, &elapsed);
    while (!elapsed) g_main_context_iteration(NULL, TRUE);
}
static GVolume *find_volume(GVolumeMonitor *monitor)
{
    GList *volumes = g_volume_monitor_get_volumes(monitor);
    GVolume *found = NULL;
    for (GList *entry = volumes; entry; entry = entry->next) {
        char *device = g_volume_get_identifier(entry->data, G_VOLUME_IDENTIFIER_KIND_UNIX_DEVICE);
        if (!g_strcmp0(device, "/dev/sda")) {
            g_assert_null(found); found = g_object_ref(entry->data);
        }
        g_free(device);
    }
    g_list_free_full(volumes, g_object_unref);
    return found;
}
static unsigned removed, added;
static void removed_event(GVolumeMonitor *monitor, GVolume *volume, gpointer data)
{
    (void)monitor;
    if (volume == data) { removed++; puts("EVENT removed original USB volume"); fflush(stdout); }
}
static void added_event(GVolumeMonitor *monitor, GVolume *volume, gpointer data)
{
    (void)monitor;
    char *device = g_volume_get_identifier(volume, G_VOLUME_IDENTIFIER_KIND_UNIX_DEVICE);
    if (!g_strcmp0(device, "/dev/sda")) {
        g_assert_true(volume != data); added++;
        puts("EVENT added distinct USB volume"); fflush(stdout);
    }
    g_free(device);
}
int main(int argc, char **argv)
{
    GVolumeMonitor *monitor = g_volume_monitor_get();
    GVolume *volume = find_volume(monitor);
    g_assert_nonnull(volume);
    GDrive *drive = g_volume_get_drive(volume);
    g_assert_nonnull(drive); g_assert_true(g_drive_is_removable(drive)); g_object_unref(drive);
    g_assert_true(g_volume_should_automount(volume));
    GMount *mount = g_volume_get_mount(volume);
    g_assert_nonnull(mount);
    GFile *root = g_mount_get_root(mount);
    GFile *file = g_file_get_child(root, "desktop-test.txt");
    const char payload[] = "MOS desktop USB read/write verification\n";
    GError *error = NULL;
    g_assert_true(g_file_replace_contents(file, payload, strlen(payload), NULL, FALSE,
                                         G_FILE_CREATE_NONE, NULL, NULL, &error));
    char *contents = NULL; gsize length;
    g_assert_true(g_file_load_contents(file, NULL, &contents, &length, NULL, &error));
    g_assert_cmpstr(contents, ==, payload); g_free(contents);
    puts("PASS automatic mount and unprivileged file read/write");
    if (argc > 1 && !strcmp(argv[1], "watch")) {
        GFileInputStream *held = g_file_read(file, NULL, &error);
        g_assert_nonnull(held);
        g_signal_connect(monitor, "volume-removed", G_CALLBACK(removed_event), volume);
        g_signal_connect(monitor, "volume-added", G_CALLBACK(added_event), volume);
        puts("READY hotplug"); fflush(stdout);
        gboolean elapsed = FALSE;
        guint timer = g_timeout_add_seconds(30, stop_wait, &elapsed);
        while (!elapsed) {
            g_main_context_iteration(NULL, TRUE);
            if (added && removed) {
                GVolume *candidate = find_volume(monitor);
                GMount *mounted = candidate ? g_volume_get_mount(candidate) : NULL;
                gboolean ready = mounted != NULL;
                g_clear_object(&mounted); g_clear_object(&candidate);
                if (ready) break;
            }
        }
        if (!elapsed) g_source_remove(timer);
        g_assert_cmpuint(removed, ==, 1); g_assert_cmpuint(added, ==, 1);
        GVolume *replacement = find_volume(monitor);
        g_assert_nonnull(replacement);
        GMount *replacement_mount = g_volume_get_mount(replacement);
        g_assert_nonnull(replacement_mount);
        GFile *new_root = g_mount_get_root(replacement_mount);
        GFile *new_file = g_file_get_child(new_root, "desktop-test.txt");
        g_assert_true(g_file_load_contents(new_file, NULL, &contents, &length, NULL, &error));
        g_assert_cmpstr(contents, ==, payload); g_free(contents);
        g_assert_true(g_file_replace_contents(new_file, payload, strlen(payload), NULL,
                                             FALSE, G_FILE_CREATE_NONE, NULL, NULL, &error));
        g_object_unref(new_file); g_object_unref(new_root); g_object_unref(replacement_mount);
        g_object_unref(held);
        g_assert_false(g_volume_can_mount(volume));
        g_assert_null(g_volume_get_mount(volume));
        g_object_unref(replacement);
        puts("PASS mounted removal, automatic mount, persistent read/write with old file held");
    } else {
        g_mount_unmount_with_operation(mount, G_MOUNT_UNMOUNT_NONE, NULL, NULL, unmount_done, NULL);
        wait_operation(); g_assert_null(g_volume_get_mount(volume));
        settle(3); g_assert_null(g_volume_get_mount(volume));
        puts("PASS manual unmount remains unmounted");
        g_volume_mount(volume, G_MOUNT_MOUNT_NONE, NULL, NULL, mount_done, NULL);
        wait_operation();
        GMount *replacement_mount = g_volume_get_mount(volume);
        g_assert_nonnull(replacement_mount);
        GFile *replacement_root = g_mount_get_root(replacement_mount);
        GFile *replacement_file = g_file_get_child(replacement_root, "desktop-test.txt");
        g_assert_true(g_file_load_contents(replacement_file, NULL, &contents, &length, NULL, &error));
        g_assert_cmpstr(contents, ==, payload); g_free(contents);
        g_object_unref(replacement_file); g_object_unref(replacement_root); g_object_unref(replacement_mount);
        puts("PASS manual remount and persistent contents");
    }
    g_object_unref(file); g_object_unref(root); g_object_unref(mount);
    g_object_unref(volume); g_object_unref(monitor);
    return 0;
}
