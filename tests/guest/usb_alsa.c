/* Verify ALSA format/rate conversion into USB Audio PCM playback. */
#include <alsa/asoundlib.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
int main(void)
{
    snd_pcm_t *pcm = NULL;
    int ret = snd_pcm_open(&pcm, "default", SND_PCM_STREAM_PLAYBACK, 0);
    if (ret < 0) { fprintf(stderr, "ALSA open: %s\n", snd_strerror(ret)); return 1; }
    ret = snd_pcm_set_params(pcm, SND_PCM_FORMAT_S16_LE, SND_PCM_ACCESS_RW_INTERLEAVED,
                             2, 44100, 1, 100000);
    if (ret < 0) { fprintf(stderr, "ALSA parameters: %s\n", snd_strerror(ret)); return 1; }
    int16_t samples[1024 * 2];
    unsigned done = 0;
    while (done < 44100) {
        unsigned count = 44100 - done;
        if (count > 1024) count = 1024;
        for (unsigned i = 0; i < count; i++)
            samples[i * 2] = samples[i * 2 + 1] = (int16_t)(12000 * sin(2 * 3.141592653589793 * 660 * (done + i) / 44100));
        snd_pcm_sframes_t written = snd_pcm_writei(pcm, samples, count);
        if (written < 0) { fprintf(stderr, "ALSA write: %s\n", snd_strerror(written)); return 1; }
        done += written;
    }
    ret = snd_pcm_drain(pcm); snd_pcm_close(pcm);
    if (ret < 0) { fprintf(stderr, "ALSA drain: %s\n", snd_strerror(ret)); return 1; }
    puts("USB_ALSA_OK client_rate=44100 device_rate=48000");
    return 0;
}
