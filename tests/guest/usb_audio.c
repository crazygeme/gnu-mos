/* Verify USB PCM playback and OSS format negotiation. */
#include <errno.h>
#include <fcntl.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/ioctl.h>
#include <sys/soundcard.h>
#include <unistd.h>

int main(int argc, char **argv)
{
    unsigned seconds = argc > 1 ? (unsigned)atoi(argv[1]) : 3;
    int fd = open("/dev/dsp", O_WRONLY);
    int format = AFMT_S16_LE, channels = 2, rate = 48000;
    if (fd < 0 || ioctl(fd, SNDCTL_DSP_SETFMT, &format) ||
        ioctl(fd, SNDCTL_DSP_CHANNELS, &channels) ||
        ioctl(fd, SNDCTL_DSP_SPEED, &rate) ||
        format != AFMT_S16_LE || channels != 2 || rate != 48000) {
        perror("USB audio format"); return 1;
    }
    int16_t samples[3072 * 2];
    unsigned total = seconds * 48000, frame = 0;
    while (frame < total) {
        unsigned frames = total - frame;
        if (frames > 3072) frames = 3072;
        for (unsigned i = 0; i < frames; i++) {
            samples[i * 2] = (int16_t)(12000 * sin(2 * 3.141592653589793 * 440 * (frame + i) / 48000));
            samples[i * 2 + 1] = samples[i * 2];
        }
        unsigned done = 0, bytes = frames * 4;
        while (done < bytes) {
            ssize_t count = write(fd, (char *)samples + done, bytes - done);
            if (count <= 0) { perror("USB isochronous write"); close(fd); return 1; }
            done += (unsigned)count;
        }
        frame += frames;
    }
    if (ioctl(fd, SNDCTL_DSP_SYNC)) { perror("USB audio drain"); return 1; }
    close(fd);
    printf("USB_AUDIO_OK rate=%d channels=%d frames=%u\n", rate, channels, frame);
    return 0;
}
