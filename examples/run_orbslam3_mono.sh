#!/usr/bin/env bash
set -e

SEQUENCE_NAME="$1"
OUTPUT_PATH="$2"

if [[ "$OUTPUT_PATH" != /* ]]; then
  OUTPUT_PATH="$(pwd)/$OUTPUT_PATH"
fi

case "$SEQUENCE_NAME" in
  euroc_mh01)
    DATASET_PATH="$HOME/vo_work/vo_vio_eval/data/euroc/MH_01_easy"
    TIMESTAMPS="$HOME/vo_work/ORB_SLAM3/Examples/Monocular/EuRoC_TimeStamps/MH01.txt"
    ORB_NAME="dataset-MH01_mono"
    ;;
  euroc_mh02)
    DATASET_PATH="$HOME/vo_work/vo_vio_eval/data/euroc/MH_02_easy"
    TIMESTAMPS="$HOME/vo_work/ORB_SLAM3/Examples/Monocular/EuRoC_TimeStamps/MH02.txt"
    ORB_NAME="dataset-MH02_mono"
    ;;
  euroc_mh03)
    DATASET_PATH="$HOME/vo_work/vo_vio_eval/data/euroc/MH_03_medium"
    TIMESTAMPS="$HOME/vo_work/ORB_SLAM3/Examples/Monocular/EuRoC_TimeStamps/MH03.txt"
    ORB_NAME="dataset-MH03_mono"
    ;;
  euroc_mh04)
    DATASET_PATH="$HOME/vo_work/vo_vio_eval/data/euroc/MH_04_difficult"
    TIMESTAMPS="$HOME/vo_work/ORB_SLAM3/Examples/Monocular/EuRoC_TimeStamps/MH04.txt"
    ORB_NAME="dataset-MH04_mono"
    ;;
  euroc_mh05)
    DATASET_PATH="$HOME/vo_work/vo_vio_eval/data/euroc/MH_05_difficult"
    TIMESTAMPS="$HOME/vo_work/ORB_SLAM3/Examples/Monocular/EuRoC_TimeStamps/MH05.txt"
    ORB_NAME="dataset-MH05_mono"
    ;;
  *)
    echo "Unknown sequence: $SEQUENCE_NAME"
    exit 1
    ;;
esac

echo "Running ORB-SLAM3 on $SEQUENCE_NAME"
echo "Dataset: $DATASET_PATH"
echo "Timestamps: $TIMESTAMPS"
echo "Output: $OUTPUT_PATH"

cd "$HOME/vo_work/ORB_SLAM3"

rm -f "f_${ORB_NAME}.txt"
rm -f "kf_${ORB_NAME}.txt"

./Examples/Monocular/mono_euroc \
  ./Vocabulary/ORBvoc.txt \
  ./Examples/Monocular/EuRoC.yaml \
  "$DATASET_PATH" \
  "$TIMESTAMPS" \
  "$ORB_NAME"

mkdir -p "$(dirname "$OUTPUT_PATH")"

RAW_OUTPUT="${OUTPUT_PATH%.txt}_raw.txt"

cp "f_${ORB_NAME}.txt" "$RAW_OUTPUT"

python "$HOME/vo_work/vo_vio_eval/src/convert_orbslam3_timestamps.py" \
  --input "$RAW_OUTPUT" \
  --output "$OUTPUT_PATH"

echo "Converted trajectory saved to $OUTPUT_PATH"