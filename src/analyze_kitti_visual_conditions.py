import argparse
from pathlib import Path

import cv2
import numpy as np
import pandas as pd


def analyze_image(image_path: Path, timestamp: float):
    img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)

    if img is None:
        return None

    blur_score = cv2.Laplacian(img, cv2.CV_64F).var()

    # Use a higher ORB cap for KITTI because 2000 saturates almost every frame.
    orb = cv2.ORB_create(nfeatures=10000)
    keypoints = orb.detect(img, None)
    texture_score = len(keypoints)

# Extra texture proxy using FAST corners, less affected by ORB's nfeatures cap.
    fast = cv2.FastFeatureDetector_create(threshold=20, nonmaxSuppression=True)
    fast_keypoints = fast.detect(img, None)
    fast_texture_score = len(fast_keypoints)

    brightness_mean = float(img.mean())
    brightness_std = float(img.std())

    return {
        "timestamp": timestamp,
        "image": str(image_path),
        "blur_score": blur_score,
        "texture_score": texture_score,
	"fast_texture_score": fast_texture_score,
        "brightness_mean": brightness_mean,
        "brightness_std": brightness_std,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-dir", required=True)
    parser.add_argument("--times-file", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    image_dir = Path(args.image_dir)
    times_file = Path(args.times_file)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    times = np.loadtxt(times_file)
    images = sorted(image_dir.glob("*.png"))

    if args.limit:
        images = images[:args.limit]

    rows = []

    for i, image_path in enumerate(images):
        frame_id = int(image_path.stem)

        if frame_id >= len(times):
            continue

        timestamp = float(times[frame_id])
        result = analyze_image(image_path, timestamp)

        if result is not None:
            rows.append(result)

        if i % 500 == 0:
            print(f"Processed {i}/{len(images)} images")

    df = pd.DataFrame(rows)
    df.to_csv(output, index=False)

    print(df.describe())
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
