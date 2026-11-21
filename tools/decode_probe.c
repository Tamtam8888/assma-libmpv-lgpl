/* Decode probe for the libmpv regression test (docs/S2_DEGISIKLIK_PLANI.md §4).
 *
 * One small program, run under Wine against two DLLs in turn (the reference release and the new build): it loads
 * libmpv-2.dll at run time, the same way ASSMA does, so the test also shows that the DLL can be swapped (LGPL).
 *
 *   decode_probe.exe <file> [af] [lavfi-complex] [pcm-output]
 *
 * It decodes the whole file as fast as possible (vo=null, untimed, no hardware decoding) and prints one line per
 * fact, "key=value": the decoders mpv chose, the number of the last video frame, the audio format, and at the end
 * "end=<reason>". With [pcm-output] the audio (after the af / lavfi-complex graph) is written to that WAV file, so
 * the samples of two DLLs can be compared byte for byte.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>
#include "mpv/client.h"

typedef mpv_handle *(*p_create)(void);
typedef int (*p_initialize)(mpv_handle *);
typedef int (*p_set_option_string)(mpv_handle *, const char *, const char *);
typedef int (*p_command)(mpv_handle *, const char **);
typedef int (*p_observe)(mpv_handle *, uint64_t, const char *, mpv_format);
typedef mpv_event *(*p_wait)(mpv_handle *, double);
typedef char *(*p_get_string)(mpv_handle *, const char *);
typedef void (*p_free)(void *);
typedef void (*p_destroy)(mpv_handle *);
typedef unsigned long (*p_api)(void);

static p_get_string get_string;
static p_free mpv_free_;

static void print_prop(mpv_handle *h, const char *name)
{
    char *v = get_string(h, name);
    printf("%s=%s\n", name, v ? v : "(unavailable)");
    if (v)
        mpv_free_(v);
}

#define LOAD(var, type, sym)                                                 \
    type var = (type)(void *)GetProcAddress(dll, sym);                       \
    if (!var) { printf("error=missing export %s\n", sym); return 3; }

int main(int argc, char **argv)
{
    if (argc < 2) {
        fprintf(stderr, "usage: decode_probe <file> [af] [lavfi-complex] [pcm-output]\n");
        return 2;
    }
    HMODULE dll = LoadLibraryA("libmpv-2.dll");
    if (!dll) {
        printf("error=libmpv-2.dll not loaded (%lu)\n", GetLastError());
        return 3;
    }
    LOAD(create, p_create, "mpv_create");
    LOAD(initialize, p_initialize, "mpv_initialize");
    LOAD(set_option, p_set_option_string, "mpv_set_option_string");
    LOAD(command, p_command, "mpv_command");
    LOAD(observe, p_observe, "mpv_observe_property");
    LOAD(wait, p_wait, "mpv_wait_event");
    LOAD(gs, p_get_string, "mpv_get_property_string");
    LOAD(fr, p_free, "mpv_free");
    LOAD(destroy, p_destroy, "mpv_terminate_destroy");
    LOAD(api, p_api, "mpv_client_api_version");
    get_string = gs;
    mpv_free_ = fr;

    printf("client_api=%lu.%lu\n", api() >> 16, api() & 0xffff);
    mpv_handle *h = create();
    if (!h) {
        printf("error=mpv_create failed\n");
        return 3;
    }
    const char *af = argc > 2 ? argv[2] : "";
    const char *lavfi = argc > 3 ? argv[3] : "";
    const char *pcm = argc > 4 ? argv[4] : "";
    set_option(h, "config", "no");
    set_option(h, "terminal", "no");
    set_option(h, "vo", "null");
    set_option(h, "untimed", "yes");
    set_option(h, "hwdec", "no");
    set_option(h, "keep-open", "yes");
    set_option(h, "audio-display", "no");
    set_option(h, "sid", "no");
    set_option(h, "ytdl", "no");
    if (*pcm) {
        set_option(h, "ao", "pcm");
        set_option(h, "ao-pcm-file", pcm);
        set_option(h, "ao-pcm-waveheader", "yes");
    } else {
        set_option(h, "ao", "null");
        set_option(h, "ao-null-untimed", "yes");
    }
    if (*af && set_option(h, "af", af) < 0)
        printf("error=af rejected\n");
    if (*lavfi && set_option(h, "lavfi-complex", lavfi) < 0)
        printf("error=lavfi-complex rejected\n");
    if (initialize(h) < 0) {
        printf("error=mpv_initialize failed\n");
        return 3;
    }
    observe(h, 1, "eof-reached", MPV_FORMAT_FLAG);
    const char *cmd[] = {"loadfile", argv[1], NULL};
    command(h, cmd);

    const char *end = "timeout";
    DWORD start = GetTickCount();
    int loaded = 0;
    while (GetTickCount() - start < 120000) {
        mpv_event *e = wait(h, 1.0);
        if (e->event_id == MPV_EVENT_FILE_LOADED) {
            loaded = 1;
        } else if (e->event_id == MPV_EVENT_PROPERTY_CHANGE) {
            mpv_event_property *p = e->data;
            if (p->format == MPV_FORMAT_FLAG && *(int *)p->data) {
                end = "eof";
                break;
            }
        } else if (e->event_id == MPV_EVENT_END_FILE) {
            mpv_event_end_file *ef = e->data;
            end = ef->reason == MPV_END_FILE_REASON_ERROR ? "error" : "end-file";
            if (ef->reason == MPV_END_FILE_REASON_ERROR)
                printf("error=end-file %d\n", ef->error);
            break;
        } else if (e->event_id == MPV_EVENT_SHUTDOWN) {
            end = "shutdown";
            break;
        }
    }
    printf("loaded=%d\n", loaded);
    print_prop(h, "file-format");
    print_prop(h, "current-tracks/video/codec");
    print_prop(h, "current-tracks/video/decoder-desc");
    print_prop(h, "width");
    print_prop(h, "height");
    print_prop(h, "video-params/pixelformat");
    print_prop(h, "estimated-frame-number");
    print_prop(h, "current-tracks/audio/codec");
    print_prop(h, "current-tracks/audio/decoder-desc");
    print_prop(h, "audio-params/format");
    print_prop(h, "audio-params/samplerate");
    print_prop(h, "audio-params/channel-count");
    print_prop(h, "audio-out-params/channel-count");
    print_prop(h, "duration");
    printf("end=%s\n", end);
    fflush(stdout);
    destroy(h); /* closes the PCM file */
    return 0;
}
