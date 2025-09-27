import cv2
import os


def segment_arabic_words(image_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    # Read the image
    image = cv2.imread(image_path)
    if image is None:
        print("Failed to load image:", image_path)
        return

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply binary inverse thresholding (text becomes white)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Dilation to group letters of a word
    # Arabic words are often more spread out horizontally
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 10))  # Adjust if needed
    dilated = cv2.dilate(binary, kernel, iterations=1)

    # Find contours (external only)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Sort from right to left (since Arabic is RTL)
    contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[0], reverse=True)

    existing_files = [f for f in os.listdir(output_dir) if f.endswith(('.png', '.jpg'))]
    existing_indices = [int(f.split('_')[1].split('.')[0]) for f in existing_files if f.startswith('word_')]
    count = max(existing_indices, default=-1) + 1

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        # Filter small noise
        if w > 20 and h > 15:
            word_img = image[y:y+h, x:x+w]
            filename = os.path.join(output_dir, f"word_{count:04d}.png")
            cv2.imwrite(filename, word_img)
            count += 1

    print(f"✅ Done! {count} word images saved in '{output_dir}'.")

#segmentation of an image
if __name__ == "__main__":
    image_path = "test.jpg"  # Replace with your image
    output_dir = "words_output"
    segment_arabic_words(image_path, output_dir)
