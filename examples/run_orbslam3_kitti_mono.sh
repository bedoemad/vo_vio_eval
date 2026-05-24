#!/usr/bin/env bash

SEQUENCE_NAME="$1"
SEQUENCE_PATH="$2"
OUTPUT_PATH="$3"

if [[ "$OUTPUT_PATH" != /* ]]; then
  OUTPUT_PATH="$(pwd)/$OUTPUT_PATH"
fi

SEQ_ID="${SEQUENCE_NAME#kitti_}"

case "$SEQ_ID" in
  00|01|02)
    SETTINGS="$HOME/vo_work/ORB_SLAM3/Examples/Monocular/KITTI00-02.yaml"
    ;;
  03)
    SETTINGS="$HOME/vo_work/ORB_SLAM3/Examples/Monocular/KITTI03.yaml"
    ;;
  04|05|06|07|08|09|10)
    SETTINGS="$HOME/vo_work/ORB_SLAM3/Examples/Monocular/KITTI04-12.yaml"
    ;;
  *)
    echo "Unknown or unsupported KITTI sequence: $SEQUENCE_NAME"
    exit 1
    ;;
esac

echo "Running ORB-SLAM3 KITTI mono"
echo "Sequence: $SEQUENCE_NAME"
echo "Path: $SEQUENCE_PATH"
echo "Settings: $SETTINGS"
echo "Output: $OUTPUT_PATH"

cd "$HOME/vo_work/ORB_SLAM3"

rm -f KeyFrameTrajectory.txt
rm -f CameraTrajectory.txt

set +e
./Examples/Monocular/mono_kitti \
  ./Vocabulary/ORBvoc.txt \
  "$SETTINGS" \
  "$SEQUENCE_PATH"
ORB_EXIT_CODE=$?
set -e

echo "ORB-SLAM3 exit code: $ORB_EXIT_CODE"

mkdir -p "$(dirname "$OUTPUT_PATH")"

RAW_OUTPUT="${OUTPUT_PATH%.txt}_raw.txt"

if [ -f "CameraTrajectory.txt" ]; then
  cp CameraTrajectory.txt "$RAW_OUTPUT"
  echo "Copied full camera trajectory to $RAW_OUTPUT"
elif [ -f "KeyFrameTrajectory.txt" ]; then
  cp KeyFrameTrajectory.txt "$RAW_OUTPUT"
  echo "Copied keyframe trajectory to $RAW_OUTPUT"
else
  echo "ERROR: no trajectory file found"
  exit "$ORB_EXIT_CODE"
fi

python "$HOME/vo_work/vo_vio_eval/src/fix_kitti_prediction_time_scale.py" \
  --input "$RAW_OUTPUT" \
  --output "$OUTPUT_PATH"

echo "Fixed trajectory saved to $OUTPUT_PATH"
ls -lh "$OUTPUT_PATH"

exit 0