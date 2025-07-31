import pytesseract
from PIL import Image
import sys
import cv2
import numpy as np

# Load image
try:
    img = Image.open('test.jpg').convert('RGB')
except FileNotFoundError:
    print("Error: Image file 'test.jpg' not found.")
    sys.exit(1)

# Convert to OpenCV format
img_cv = np.array(img)
img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)

# Apply thresholding to improve contrast
_, img_thresh = cv2.threshold(img_cv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

# Convert back to PIL for pytesseract
img_pil = Image.fromarray(img_thresh)

# OCR
text = pytesseract.image_to_string(img_pil, lang='ara')

if not text.strip():
    print("No Arabic text detected. Trying without language spec...")
    text = pytesseract.image_to_string(img_pil)

print("OCR result:")
print(text if text.strip() else "No text detected.")
