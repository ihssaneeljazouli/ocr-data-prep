import os
import cv2
from preprocessor import preprocess

# === PARAMÈTRES ===
IMAGE_WIDTH = 128
IMAGE_HEIGHT = 32
MAX_TEXT_LENGTH = 32

# === CHEMINS ===
images_dir = "arabic_data_generator/images"
labels_dir = "arabic_data_generator/labels"
output_bin_path = "binary_dataset/my_dataset.bin"
output_txt_path = "binary_dataset/my_dataset.txt"

os.makedirs("binary_dataset", exist_ok=True)

# === TRAITEMENT ===
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
        
        # Lire image
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"⚠️ Could not read {image_path}")
            continue
        
        # Prétraitement
        img = preprocess(img, image_width=IMAGE_WIDTH, image_height=IMAGE_HEIGHT)
        
        # Normalisation sécurisée
        if img.max() != img.min():
            img = ((img - img.min()) * (255.0 / (img.max() - img.min()))).astype('uint8')
        else:
            img = img.astype('uint8')
        
        # preprocess retourne (128, 32)
        if img.shape != (128, 32):
            print(f"⚠️ Unexpected image size: {image_filename} got {img.shape}")
            continue
        
        # TRANSPOSER pour que l'extracteur la lise correctement
        img = cv2.transpose(img)  # Maintenant (32, 128)
        
        h, w = img.shape  # h=32, w=128
        img_bytes = img.tobytes()
        
        # Lire le label
        with open(label_path, 'r', encoding='utf-8') as f:
            word = f.read().strip()
        
        if not word or len(word) > MAX_TEXT_LENGTH:
            print(f"⚠️ Invalid or too long label for {image_filename}: '{word}'")
            continue
        
        # Écriture dans le .bin
        bin_f.write(img_bytes)
        
        # Écriture dans le .txt (h=32, w=128)
        txt_f.write(
            f"image idx:{index};start position:{byte_offset};"
            f"image height:{h};image width:{w};"
            f"font name:Custom;font size:26;"
            f"bold:false;italic:false;word:{word}\n"
        )
        
        index += 1
        byte_offset += len(img_bytes)

print(f"✅ Done: wrote {index} images to {output_bin_path} and labels to {output_txt_path}")