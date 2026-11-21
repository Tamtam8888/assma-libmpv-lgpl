#!/usr/bin/env bash
# Test files for the decode regression test (docs/S2_DEGISIKLIK_PLANI.md §4).
# Made fresh on the CI runner with the runner's own ffmpeg, 3 seconds each, from FFmpeg's test sources; nothing is
# downloaded and nothing goes into a release. A format the runner's ffmpeg cannot encode is skipped and listed.
#
#   make_test_media.sh <output folder>
set -u
out="${1:?output folder}"
mkdir -p "$out"
V="-f lavfi -i testsrc2=size=640x360:rate=25:duration=3"
V50="-f lavfi -i testsrc2=size=1920x1080:rate=25:duration=3"
A="-f lavfi -i sine=frequency=440:sample_rate=48000:duration=3"
# 8 channels, each its own tone, so a wrong channel route changes the samples
A8="-f lavfi -i aevalsrc=sin(220*t*2*PI)|sin(330*t*2*PI)|sin(440*t*2*PI)|sin(550*t*2*PI)|sin(660*t*2*PI)|sin(770*t*2*PI)|sin(880*t*2*PI)|sin(990*t*2*PI):s=48000:d=3:c=7.1"
made=() skipped=()

mk() {  # name, then ffmpeg arguments
    local name="$1"; shift
    if ffmpeg -hide_banner -loglevel error -y "$@" "$out/$name" 2>"$out/$name.log"; then
        made+=("$name"); rm -f "$out/$name.log"
    else
        skipped+=("$name ($(head -c 200 "$out/$name.log" | tr '\n' ' '))"); rm -f "$out/$name" "$out/$name.log"
    fi
}

# video (+ audio)
mk h264_high_aac.mp4      $V $A -c:v libx264 -profile:v high -pix_fmt yuv420p -c:a aac -b:a 128k
mk hevc_main10.mkv        $V -c:v libx265 -pix_fmt yuv420p10le -x265-params log-level=error
mk mpeg2_422_xdcam.mxf    $V50 $A -c:v mpeg2video -pix_fmt yuv422p -b:v 50M -maxrate 50M -minrate 50M -bufsize 17M \
                          -flags +ildct+ilme -top 1 -g 12 -c:a pcm_s24le -ar 48000
mk prores422.mov          $V $A -c:v prores_ks -profile:v 2 -c:a pcm_s24le
mk dnxhd.mxf              $V50 $A -c:v dnxhd -b:v 120M -pix_fmt yuv422p -c:a pcm_s16le -ar 48000
mk vp9_opus.mkv           $V $A -c:v libvpx-vp9 -b:v 1M -deadline realtime -cpu-used 8 -c:a libopus
mk av1.mkv                $V -c:v libaom-av1 -cpu-used 8 -b:v 500k -row-mt 1
mk av1_svt.mkv            $V -c:v libsvtav1 -preset 12
mk vvc.mp4                $V -c:v libvvenc
mk h264_ac3.ts            $V $A -c:v libx264 -pix_fmt yuv420p -c:a ac3 -f mpegts
mk mpeg4_mp3.avi          $V $A -c:v mpeg4 -q:v 5 -c:a libmp3lame
# audio
mk aac.m4a                $A -c:a aac
mk ac3.ac3                $A -c:a ac3
mk eac3.eac3              $A -c:a eac3
mk mp2.mp2                $A -c:a mp2
mk mp3.mp3                $A -c:a libmp3lame
mk flac.flac              $A -c:a flac
mk vorbis.ogg             $A -c:a libvorbis
mk pcm24.wav              $A -c:a pcm_s24le
mk pcm24.mxf              $V50 $A -c:v mpeg2video -pix_fmt yuv422p -b:v 30M -c:a pcm_s24le -ar 48000
mk pcm8ch.wav             $A8 -c:a pcm_s24le
# two audio tracks (5.1-ish 8 channel + stereo): input for ASSMA's lavfi-complex / amerge graph
mk two_tracks.mkv         $V $A8 $A -map 0:v -map 1:a -map 2:a -c:v libx264 -pix_fmt yuv420p -c:a pcm_s16le

printf '%s\n' "${made[@]}" > "$out/MADE.txt"
printf '%s\n' "${skipped[@]}" > "$out/SKIPPED.txt"
echo "made: ${#made[@]}  skipped: ${#skipped[@]}"
[ ${#skipped[@]} -eq 0 ] || { echo "skipped:"; cat "$out/SKIPPED.txt"; }
