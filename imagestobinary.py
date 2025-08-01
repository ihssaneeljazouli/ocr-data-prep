import os
import cv2

# === INPUT PATHS ===
images_dir = "dataset/images"
labels_dir = "dataset/labels"
output_bin_path = "binary_dataset/my_dataset.bin"
output_txt_path = "binary_dataset/my_dataset.txt"

# === OUTPUT FILES ===
with open(output_bin_path, "wb") as bin_f, open(output_txt_path, "w", encoding="utf-8") as txt_f:
    index = 0
    byte_offset = 0

    for image_filename in sorted(os.listdir(images_dir)):
        if not image_filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue

        base = os.path.splitext(image_filename)[0]
        image_path = os.path.join(images_dir, image_filename)
        label_path = os.path.join(labels_dir, base + ".txt")

        if not os.path.isfile(label_path):
            print(f"⚠️ No label for {image_filename}, skipping.")
            continue

        # Load image
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"⚠️ Could not read {image_path}")
            continue

        h, w = img.shape
        img_bytes = img.tobytes()

        # Read label
        with open(label_path, 'r', encoding='utf-8') as f:
            word = f.read().strip()

        # Write raw image bytes to binary file
        bin_f.write(img_bytes)

        # Write metadata line to txt file
        txt_f.write(
            f"image idx:{index};start position:{byte_offset};"
            f"image height:{h};image width:{w};"
            f"font name:Custom;font size:26;"
            f"bold:false;italic:false;word:{word}\n"
        )

        # Update index and byte offset
        index += 1
        byte_offset += len(img_bytes)

print(f"✅ Done: wrote {index} images to {output_bin_path} and labels to {output_txt_path}")
