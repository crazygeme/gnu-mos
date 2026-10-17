/* Verify ALSA card enumeration, mixer values and control notifications. */
#include <alsa/asoundlib.h>
#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>

static void check(int ret, const char *op)
{
    if (ret < 0) { fprintf(stderr, "%s: %s\n", op, snd_strerror(ret)); exit(1); }
}
static void require(int ok, const char *op)
{
    if (!ok) { fprintf(stderr, "%s\n", op); exit(1); }
}
int main(void)
{
    int card = -1;
    check(snd_card_next(&card), "card enumeration");
    require(card == 0, "Card zero is unavailable");
    snd_ctl_t *ctl;
    check(snd_ctl_open(&ctl, "hw:0", SND_CTL_NONBLOCK), "control open");
    snd_ctl_card_info_t *info;
    snd_ctl_card_info_alloca(&info);
    check(snd_ctl_card_info(ctl, info), "card info");
    int device = -1;
    check(snd_ctl_pcm_next_device(ctl, &device), "PCM enumeration");
    require(device == 0, "PCM zero is unavailable");
    snd_pcm_info_t *pcm;
    snd_pcm_info_alloca(&pcm);
    snd_pcm_info_set_device(pcm, device);
    snd_pcm_info_set_stream(pcm, SND_PCM_STREAM_PLAYBACK);
    check(snd_ctl_pcm_info(ctl, pcm), "PCM information");
    snd_ctl_elem_list_t *list;
    snd_ctl_elem_list_alloca(&list);
    check(snd_ctl_elem_list(ctl, list), "element count");
    require(snd_ctl_elem_list_get_count(list) == 2, "Unexpected mixer element count");
    check(snd_ctl_elem_list_alloc_space(list, 2), "element allocation");
    check(snd_ctl_elem_list(ctl, list), "element enumeration");
    check(snd_ctl_subscribe_events(ctl, 1), "event subscription");
    snd_ctl_elem_value_t *value;
    snd_ctl_elem_value_alloca(&value);
    snd_ctl_elem_value_set_numid(value, 1);
    check(snd_ctl_elem_read(ctl, value), "volume read");
    long left = snd_ctl_elem_value_get_integer(value, 0);
    long right = snd_ctl_elem_value_get_integer(value, 1);
    snd_ctl_elem_value_set_integer(value, 0, left == 73 ? 74 : 73);
    snd_ctl_elem_value_set_integer(value, 1, right == 73 ? 74 : 73);
    check(snd_ctl_elem_write(ctl, value), "volume write");
    struct pollfd fd;
    require(snd_ctl_poll_descriptors(ctl, &fd, 1) == 1, "Control poll descriptor is unavailable");
    struct stat status;
    require(fstat(fd.fd, &status) == 0 && major(status.st_rdev) == 116 &&
            minor(status.st_rdev) == 0, "Invalid control device number");
    require(poll(&fd, 1, 1000) == 1 && (fd.revents & POLLIN), "Mixer event was not delivered");
    snd_ctl_event_t *event;
    snd_ctl_event_alloca(&event);
    check(snd_ctl_read(ctl, event), "event read");
    require(snd_ctl_event_elem_get_numid(event) == 1, "Unexpected mixer event");
    snd_ctl_elem_value_set_integer(value, 0, left);
    snd_ctl_elem_value_set_integer(value, 1, right);
    check(snd_ctl_elem_write(ctl, value), "volume restoration");
    snd_pcm_t *stream;
    check(snd_pcm_open(&stream, "hw:0,0", SND_PCM_STREAM_PLAYBACK, 0), "PCM open");
    snd_pcm_hw_params_t *params;
    snd_pcm_hw_params_alloca(&params);
    check(snd_pcm_hw_params_any(stream, params), "hardware constraints");
    require(snd_pcm_hw_params_test_rate(stream, params, 44100, 0) < 0,
            "Native PCM accepted an unsupported rate");
    require(snd_pcm_hw_params_test_format(stream, params, SND_PCM_FORMAT_FLOAT_LE) < 0,
            "Native PCM accepted an unsupported format");
    check(snd_pcm_set_params(stream, SND_PCM_FORMAT_S16_LE,
          SND_PCM_ACCESS_RW_INTERLEAVED, 2, 48000, 0, 100000), "PCM setup");
    check(snd_pcm_nonblock(stream, 1), "nonblocking mode");
    static short silence[4800 * 2];
    require(snd_pcm_writei(stream, silence, 4800) == 4800, "Initial PCM fill failed");
    require(snd_pcm_writei(stream, silence, 1) == -EAGAIN, "Full PCM did not return EAGAIN");
    usleep(250000);
    require(snd_pcm_state(stream) == SND_PCM_STATE_XRUN, "Underrun state is unavailable");
    require(snd_pcm_writei(stream, silence, 1) == -EPIPE, "Underrun did not return EPIPE");
    require(snd_pcm_drain(stream) == -EPIPE, "Underrun drain did not return EPIPE");
    check(snd_pcm_prepare(stream), "underrun recovery");
    require(snd_pcm_state(stream) == SND_PCM_STATE_PREPARED, "PCM recovery did not prepare the stream");
    require(snd_pcm_writei(stream, silence, 4800) == 4800, "PCM recovery fill failed");
    require(snd_pcm_drain(stream) == -EAGAIN, "Nonblocking drain did not return EAGAIN");
    usleep(250000);
    check(snd_pcm_drain(stream), "drain completion");
    require(snd_pcm_state(stream) == SND_PCM_STATE_SETUP, "Drained PCM remained active");
    check(snd_pcm_drop(stream), "PCM drop");
    check(snd_pcm_close(stream), "PCM close");
    printf("ALSA_CONTROL_OK card=%s elements=2 notifications=1 nonblock=1 xrun_recovery=1\n", snd_ctl_card_info_get_name(info));
    snd_ctl_elem_list_free_space(list);
    check(snd_ctl_close(ctl), "control close");
    return 0;
}
