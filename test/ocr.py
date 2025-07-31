import pytesseract
from PIL import Image
import cv2
import os


# Load the image (example: 'arabic_text.jpg')
image_path = "maroc.jpg"
img = cv2.imread(image_path)

# Convert to grayscale (better for OCR)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# (Optional) Apply thresholding to enhance contrast
# gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

# Use Tesseract to extract Arabic text
custom_config = r'-l ara --psm 6'  # -l ara = Arabic, --psm 6 = assume a uniform block of text
text = pytesseract.image_to_string(gray, config=custom_config)

print("📄 Extracted Arabic Text:")
print(text)
