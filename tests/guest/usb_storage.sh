#!/bin/sh
# Run as root with an unmounted USB device containing an ext3 filesystem.
set -eu
device=${1:-/dev/sda}
mount_dir=/mnt/usb-test-$$
source_file=/tmp/usb-source-$$
mounted=0
cleanup() {
    if [ "$mounted" = 1 ]; then umount "$mount_dir"; fi
    rm -f "$source_file"
    rmdir "$mount_dir" 2>/dev/null || true
}
trap cleanup EXIT HUP INT TERM
mkdir -p "$mount_dir"
mount -t ext3 "$device" "$mount_dir"
mounted=1
test_dir=$(mktemp -d "$mount_dir/.usb-test-XXXXXX")
name=${test_dir##*/}
dd if=/dev/urandom of="$source_file" bs=4096 count=256 status=none
cp "$source_file" "$test_dir/payload"
expected=$(sha256sum "$source_file")
expected=${expected%% *}
actual=$(sha256sum "$test_dir/payload")
[ "${actual%% *}" = "$expected" ]
printf 'USB_WRITE_READ_OK %s\n' "$expected"
sync
umount "$mount_dir"
mounted=0
mount -t ext3 "$device" "$mount_dir"
mounted=1
actual=$(sha256sum "$mount_dir/$name/payload")
[ "${actual%% *}" = "$expected" ]
printf 'USB_REMOUNT_OK %s\n' "$expected"
rm -rf "$mount_dir/$name"
sync
umount "$mount_dir"
mounted=0
