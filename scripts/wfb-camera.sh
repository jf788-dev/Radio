#!/bin/bash
source /etc/default/wfb-camera

exec /usr/bin/rpicam-vid -t 0 -n \
  --width "$WIDTH" --height "$HEIGHT" \
  --framerate "$FRAMERATE" \
  --codec libav \
  --libav-format h264 \
  --bitrate "$BITRATE" \
  --intra 20 \
  --profile baseline \
  --level 4.0 \
  --inline \
  --flush \
  --low-latency \
  --awb auto \
  --autofocus-mode manual \
  --lens-position "$LENS_POSITION" \
  --denoise cdn_fast \
  -o udp://127.0.0.1:5602
