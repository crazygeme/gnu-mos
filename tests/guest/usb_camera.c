/* Validate V4L2 mmap capture, queue reuse, and nonempty UVC frames. */
#include <errno.h>
#include <fcntl.h>
#include <linux/videodev2.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <unistd.h>
int main(int argc, char **argv)
{
    unsigned frames = argc > 1 ? (unsigned)atoi(argv[1]) : 20;
    int mjpeg = argc > 2 && !strcmp(argv[2], "MJPG");
    int unplug = argc > 3 && !strcmp(argv[3], "disconnect");
    int fd = open("/dev/video0", O_RDWR);
    struct v4l2_capability cap;
    struct v4l2_format format = {.type = V4L2_BUF_TYPE_VIDEO_CAPTURE};
    format.fmt.pix.width = 320; format.fmt.pix.height = 240;
    format.fmt.pix.pixelformat = mjpeg ? V4L2_PIX_FMT_MJPEG : V4L2_PIX_FMT_YUYV; format.fmt.pix.field = V4L2_FIELD_NONE;
    if (fd < 0 || ioctl(fd, VIDIOC_QUERYCAP, &cap) ||
        !(cap.capabilities & V4L2_CAP_STREAMING) || ioctl(fd, VIDIOC_S_FMT, &format)) {
        perror("V4L2 initialization"); return 1;
    }
    struct v4l2_requestbuffers request = {.count = 4, .type = V4L2_BUF_TYPE_VIDEO_CAPTURE, .memory = V4L2_MEMORY_MMAP};
    if (ioctl(fd, VIDIOC_REQBUFS, &request)) { perror("V4L2 buffers"); return 1; }
    void *buffers[4]; unsigned lengths[4];
    for (unsigned i = 0; i < request.count; i++) {
        struct v4l2_buffer b = {.index = i, .type = V4L2_BUF_TYPE_VIDEO_CAPTURE, .memory = V4L2_MEMORY_MMAP};
        if (ioctl(fd, VIDIOC_QUERYBUF, &b)) { perror("V4L2 query buffer"); return 1; }
        buffers[i] = mmap(NULL, b.length, PROT_READ | PROT_WRITE, MAP_SHARED, fd, b.m.offset);
        lengths[i] = b.length;
        if (buffers[i] == MAP_FAILED || ioctl(fd, VIDIOC_QBUF, &b)) { perror("V4L2 queue buffer"); return 1; }
    }
    enum v4l2_buf_type type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    if (ioctl(fd, VIDIOC_STREAMON, &type)) { perror("V4L2 stream on"); return 1; }
    setvbuf(stdout, NULL, _IONBF, 0);
    puts("USB_CAMERA_STREAMING");
    for (unsigned i = 0; i < frames; i++) {
        struct v4l2_buffer b = {.type = type, .memory = V4L2_MEMORY_MMAP};
        if (ioctl(fd, VIDIOC_DQBUF, &b)) { perror("V4L2 dequeue"); return 1; }
        if (b.index >= request.count || (!mjpeg && b.bytesused != format.fmt.pix.sizeimage) || !b.bytesused || b.bytesused > lengths[b.index]) {
            fprintf(stderr, "Invalid frame index=%u bytes=%u expected=%u\n", b.index, b.bytesused, format.fmt.pix.sizeimage); return 1;
        }
        if (mjpeg && (b.bytesused < 4 || ((unsigned char *)buffers[b.index])[0] != 0xff || ((unsigned char *)buffers[b.index])[1] != 0xd8)) {
            fprintf(stderr, "Invalid JPEG header\n"); return 1;
        }
        uint32_t checksum = 0;
        unsigned char *pixels = buffers[b.index];
        for (unsigned j = 0; j < b.bytesused; j++) checksum = checksum * 33 + pixels[j];
        printf("USB_CAMERA_FRAME %u sequence=%u bytes=%u checksum=%08x\n", i, b.sequence, b.bytesused, checksum);
        if (ioctl(fd, VIDIOC_QBUF, &b)) { perror("V4L2 requeue"); return 1; }
    }
    if (unplug) {
        puts("USB_CAMERA_REMOVE_READY");
        for (;;) {
            struct v4l2_buffer b = {.type = type, .memory = V4L2_MEMORY_MMAP};
            if (ioctl(fd, VIDIOC_DQBUF, &b)) {
                if (errno != ENODEV) { perror("V4L2 removal"); return 1; }
                break;
            }
        }
        volatile unsigned char retained = *(unsigned char *)buffers[0];
        (void)retained;
        for (unsigned i = 0; i < request.count; i++) munmap(buffers[i], lengths[i]);
        close(fd); puts("USB_CAMERA_DISCONNECT_OK"); return 0;
    }
    if (ioctl(fd, VIDIOC_STREAMOFF, &type)) { perror("V4L2 stream off"); return 1; }
    for (unsigned i = 0; i < request.count; i++) munmap(buffers[i], lengths[i]);
    request.count = 0;
    if (ioctl(fd, VIDIOC_REQBUFS, &request)) { perror("V4L2 release buffers"); return 1; }
    close(fd); puts("USB_CAMERA_MMAP_OK"); return 0;
}
