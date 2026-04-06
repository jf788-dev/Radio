#!/bin/bash
set -eu

WIDTH="${WIDTH:-1280}"
HEIGHT="${HEIGHT:-720}"
FRAMERATE="${FRAMERATE:-30}"
BITRATE="${BITRATE:-3000000}"
LENS_POSITION="${LENS_POSITION:-0.0}"

if [ -f /etc/default/wfb-camera ]; then
  # Allow host overrides while keeping sane startup defaults on a fresh install.
  # shellcheck disable=SC1091
  source /etc/default/wfb-camera
fi

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
