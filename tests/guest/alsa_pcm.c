/* Validate native ALSA PCM playback and frame accounting. */
#include <alsa/asoundlib.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static void check(int ret, const char *op)
{
    if (ret < 0) { fprintf(stderr, "%s: %s\n", op, snd_strerror(ret)); exit(1); }
}
int main(int argc, char **argv)
{
    const char *device = argc > 1 ? argv[1] : "hw:0,0";
    unsigned rate = argc > 2 ? atoi(argv[2]) : 48000;
    unsigned seconds = argc > 3 ? atoi(argv[3]) : 10;
    int mmap_mode = argc > 4 && atoi(argv[4]);
    snd_pcm_t *pcm;
    check(snd_pcm_open(&pcm, device, SND_PCM_STREAM_PLAYBACK, 0), "open");
    check(snd_pcm_set_params(pcm, SND_PCM_FORMAT_S16_LE,
          mmap_mode ? SND_PCM_ACCESS_MMAP_INTERLEAVED : SND_PCM_ACCESS_RW_INTERLEAVED,
          2, rate, 1, argc > 5 ? atoi(argv[5]) : 100000), "parameters");
    snd_output_t *out;
    check(snd_output_stdio_attach(&out, stdout, 0), "output");
    snd_pcm_dump(pcm, out);
    int16_t samples[1024 * 2];
    unsigned done = 0, xruns = 0;
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    while (done < rate * seconds) {
        unsigned count = rate * seconds - done;
        if (count > 1024) count = 1024;
        for (unsigned i = 0; i < count; i++) {
            double fade = 1;
            if (done + i < rate / 100) fade = (double)(done + i) / (rate / 100);
            if (rate * seconds - done - i < rate / 100)
                fade = (double)(rate * seconds - done - i) / (rate / 100);
            samples[i * 2] = samples[i * 2 + 1] =
                (int16_t)(10000 * fade * sin(2 * 3.141592653589793 * 660 * (done + i) / rate));
        }
        snd_pcm_sframes_t n = mmap_mode ? snd_pcm_mmap_writei(pcm, samples, count) :
                                         snd_pcm_writei(pcm, samples, count);
        if (n == -EPIPE) { xruns++; check(snd_pcm_prepare(pcm), "recover"); continue; }
        check(n, "write");
        if (!n) { fprintf(stderr, "write returned zero\n"); return 1; }
        done += n;
    }
    check(snd_pcm_drain(pcm), "drain");
    clock_gettime(CLOCK_MONOTONIC, &end);
    double elapsed = end.tv_sec - start.tv_sec + (end.tv_nsec - start.tv_nsec) / 1e9;
    printf("ALSA_PCM_OK device=%s rate=%u frames=%u mmap=%d xruns=%u elapsed=%.6f\n",
           device, rate, done, mmap_mode, xruns, elapsed);
    check(snd_pcm_close(pcm), "close");
    snd_output_close(out);
    return xruns || elapsed < seconds * .98 || elapsed > seconds * 1.05;
}
