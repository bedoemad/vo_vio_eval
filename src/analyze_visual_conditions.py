import argparse
from pathlib import Path

import cv2
import pandas as pd


def analyze_image(image_path: Path):
    img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)

    if img is None:
        return None

    blur_score = cv2.Laplacian(img, cv2.CV_64F).var()

    orb = cv2.ORB_create(nfeatures=2000)
    keypoints = orb.detect(img, None)
    texture_score = len(keypoints)

    brightness_mean = float(img.mean())
    brightness_std = float(img.std())

    timestamp_ns = image_path.stem
    timestamp_sec = float(timestamp_ns) * 1e-9

    return {
        "timestamp": timestamp_sec,
        "image": str(image_path),
        "blur_score": blur_score,
        "texture_score": texture_score,
        "brightness_mean": brightness_mean,
        "brightness_std": brightness_std,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    image_dir = Path(args.image_dir)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    images = sorted(list(image_dir.glob("*.png")))

    if args.limit:
        images = images[:args.limit]

    rows = []

    for i, image_path in enumerate(images):
        result = analyze_image(image_path)
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
