#!/bin/sh
# Validate the configured Docker runtime in a MOS guest.
set -eu
image=${DOCKER_TEST_IMAGE:-busybox:1.37.0}
container=mos-smoke-$$
volume=$(mktemp -d /tmp/mos-docker-smoke.XXXXXX)
cleanup()
{
    docker rm -f "$container" >/dev/null 2>&1 || true
    rm -rf "$volume"
}
trap cleanup 0
/etc/init.d/docker start
if ! docker image inspect "$image" >/dev/null 2>&1; then
    docker pull "$image"
fi
[ "$(docker run --rm --network host "$image" echo MOS_DOCKER_OK)" = MOS_DOCKER_OK ]
docker run -d --name "$container" --hostname mos-container --network host --pids-limit 32 \
    "$image" sh -c 'echo MOS_LOG_OK; sleep 120' >/dev/null
docker exec "$container" sh -c 'test "$(hostname)" = mos-container; test "$(head -c 1 /proc/1/stat)" = 1'
docker exec "$container" sh -c \
    'mknod /dev/mos-forbidden c 1 1; if head -c 1 /dev/mos-forbidden; then exit 1; fi; echo permitted >/dev/null'
[ "$(docker logs "$container")" = MOS_LOG_OK ]
printf MOS_VOLUME_IN > "$volume/input"
ln -s input "$volume/link"
docker run --rm --network host -v "$volume:/data" "$image" sh -c \
    'test "$(cat /data/link)" = MOS_VOLUME_IN; echo MOS_VOLUME_OUT > /data/output'
[ "$(cat "$volume/output")" = MOS_VOLUME_OUT ]
docker run --rm --network host -v "$volume:/data:ro" "$image" sh -c \
    'test "$(cat /data/link)" = MOS_VOLUME_IN; if echo invalid > /data/output; then exit 1; fi'
[ "$(cat "$volume/output")" = MOS_VOLUME_OUT ]
docker run --rm --network host --read-only "$image" sh -c \
    'if touch /mos-readonly-probe; then exit 1; fi; test ! -e /mos-readonly-probe'
[ "$(docker run --rm --network host --user 1000:1000 "$image" id -u)" = 1000 ]
docker stop -t 3 "$container" >/dev/null
docker rm "$container" >/dev/null
if [ "${DOCKER_TEST_RESTART:-0}" = 1 ]; then
    /etc/init.d/docker restart
    [ "$(docker run --rm --network host "$image" echo MOS_RESTART_OK)" = MOS_RESTART_OK ]
fi
printf '%s\n' 'Docker container lifecycle, isolation, volumes and permissions: PASS'
