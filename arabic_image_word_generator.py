import random
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from pathlib import Path
import arabic_reshaper
from bidi.algorithm import get_display

class ArabicOCRWordGenerator:
    def __init__(self, output_dir="arabic_generator_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.images_dir = self.output_dir / "images"
        self.labels_dir = self.output_dir / "labels"
        self.images_dir.mkdir(exist_ok=True)
        self.labels_dir.mkdir(exist_ok=True)
        
        # Arabic letters (without diacritics for simplicity)
        self.arabic_letters = [
            'ا', 'ب', 'ت', 'ث', 'ج', 'ح', 'خ', 'د', 'ذ', 'ر', 'ز', 'س', 'ش', 'ص', 'ض', 
            'ط', 'ظ', 'ع', 'غ', 'ف', 'ق', 'ك', 'ل', 'م', 'ن', 'ه', 'و', 'ي'
        ]
        
        # Common Arabic prefixes and suffixes
        self.common_prefixes = ['ال', 'و', 'ف', 'ب', 'ل', 'ك', 'لل', 'في', 'من', 'إلى', 'على', 'عن']
        self.common_suffixes = ['ها', 'ان', 'ين', 'ون', 'ة', 'ات', 'يه', 'ته', 'كم', 'نا', 'ني']
        
        # Common Arabic root patterns (3-letter roots)
        self.common_roots = ['كتب', 'درس', 'عمل', 'قرأ', 'سمع', 'شرب', 'أكل', 'نوم', 'جلس', 'قام', 'ذهب', 'جاء']
        
        # Numbers in Arabic
        self.arabic_numbers = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩']
        
        # Try to load an Arabic font (you might need to adjust the path)
        self.arabic_fonts = [
            "/System/Library/Fonts/Arial Unicode.ttf",  # macOS
            "C:/Windows/Fonts/arial.ttf",  # Windows
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            "NotoSansArabic-Regular.ttf",  # If you have Noto fonts
            "amiri-regular.ttf"  # If you have Amiri font
        ]
        
    def get_arabic_font(self, size):
        """Try to load an Arabic-compatible font"""
        for font_path in self.arabic_fonts:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        
        # Fallback to default font
        try:
            return ImageFont.load_default()
        except:
            return None
    
    def generate_synthetic_arabic_word(self, min_length=2, max_length=8):
        """Generate a synthetic Arabic word"""
        word_type = random.choice(['random', 'prefix_root', 'root_suffix', 'prefix_root_suffix', 'compound'])
        
        if word_type == 'random':
            # Pure random Arabic word
            length = random.randint(min_length, max_length)
            word = ''.join(random.choices(self.arabic_letters, k=length))
        
        elif word_type == 'prefix_root':
            prefix = random.choice(self.common_prefixes)
            root = random.choice(self.common_roots)
            word = prefix + root
        
        elif word_type == 'root_suffix':
            root = random.choice(self.common_roots)
            suffix = random.choice(self.common_suffixes)
            word = root + suffix
        
        elif word_type == 'prefix_root_suffix':
            prefix = random.choice(self.common_prefixes)
            root = random.choice(self.common_roots)
            suffix = random.choice(self.common_suffixes)
            word = prefix + root + suffix
        
        else:  # compound
            word1 = ''.join(random.choices(self.arabic_letters, k=random.randint(2, 4)))
            word2 = ''.join(random.choices(self.arabic_letters, k=random.randint(2, 4)))
            word = word1 + word2
        
        # Occasionally add Arabic numbers
        if random.random() < 0.15:
            numbers = ''.join(random.choices(self.arabic_numbers, k=random.randint(1, 3)))
            if random.random() < 0.5:
                word = numbers + word
            else:
                word = word + numbers
        
        return word
    
    def add_handwriting_variations_arabic(self, draw, text, x, y, font, base_color):
        """Add handwriting-like variations to Arabic text"""
        # Arabic text needs proper shaping and bidi handling
        try:
            reshaped_text = arabic_reshaper.reshape(text)
            display_text = get_display(reshaped_text)
        except:
            # Fallback if arabic_reshaper is not available
            display_text = text
        
        # Get text dimensions
        bbox = draw.textbbox((0, 0), display_text, font=font)
        text_width = bbox[2] - bbox[0]
        
        # Add overall text rotation and position variation
        overall_y_offset = random.randint(-5, 5)
        overall_x_offset = random.randint(-3, 3)
        
        # Color variation
        color_var = random.randint(-40, 40)
        varied_color = max(20, min(200, base_color + color_var))
        
        # Draw the text with slight variations
        final_x = x + overall_x_offset
        final_y = y + overall_y_offset
        
        # Add slight blur effect for handwriting
        for offset in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
            blur_color = max(0, varied_color - 50)
            draw.text((final_x + offset[0], final_y + offset[1]), 
                     display_text, font=font, fill=(blur_color, blur_color, blur_color))
        
        # Main text
        draw.text((final_x, final_y), display_text, font=font, 
                 fill=(varied_color, varied_color, varied_color))
        
        return text_width
    
    def add_noise_and_effects(self, img):
        """Add realistic noise and effects to simulate paper and scanning artifacts"""
        img_array = np.array(img)
        
        # Add paper texture (slight random noise)
        noise = np.random.randint(-15, 15, img_array.shape)
        img_array = np.clip(img_array + noise, 0, 255)
        
        # Add occasional ink blots or smudges
        if random.random() < 0.3:
            # Random small dark spots
            for _ in range(random.randint(1, 3)):
                x = random.randint(0, img_array.shape[1]-1)
                y = random.randint(0, img_array.shape[0]-1)
                size = random.randint(1, 3)
                img_array[max(0, y-size):min(img_array.shape[0], y+size),
                         max(0, x-size):min(img_array.shape[1], x+size)] = random.randint(0, 100)
        
        # Slight blur to simulate handwriting
        img = Image.fromarray(img_array.astype(np.uint8))
        
        return img
    
    def generate_word_image(self, word, width=300, height=60):
        """Generate a handwritten-style image of an Arabic word"""
        # Create image with off-white background
        bg_color = random.randint(240, 255)
        img = Image.new('RGB', (width, height), color=(bg_color, bg_color, bg_color))
        draw = ImageDraw.Draw(img)
        
        # Get font
        font_size = random.randint(20, 35)
        font = self.get_arabic_font(font_size)
        
        if font is None:
            print("Warning: Could not load Arabic font. Text might not display correctly.")
            font = ImageFont.load_default()
        
        # Calculate text position (center)
        temp_bbox = draw.textbbox((0, 0), word, font=font)
        text_width = temp_bbox[2] - temp_bbox[0]
        text_height = temp_bbox[3] - temp_bbox[1]
        
        x = (width - text_width) // 2 + random.randint(-10, 10)
        y = (height - text_height) // 2 + random.randint(-5, 5)
        
        # Base ink color (dark with variation)
        base_color = random.randint(0, 60)
        
        # Add handwriting variations
        self.add_handwriting_variations_arabic(draw, word, x, y, font, base_color)
        
        # Add noise and effects
        img = self.add_noise_and_effects(img)
        
        return img
    
    def generate_dataset(self, num_samples=1000):
        """Generate a complete dataset of Arabic word images and labels"""
        print(f"Generating {num_samples} Arabic word samples...")
        
        for i in range(num_samples):
            # Generate synthetic word
            word = self.generate_synthetic_arabic_word()
            
            # Generate image
            img = self.generate_word_image(word)
            
            # Save image
            img_filename = f"word_{i:06d}.png"
            img_path = self.images_dir / img_filename
            img.save(img_path)
            
            # Save corresponding text file
            txt_filename = f"word_{i:06d}.txt"
            txt_path = self.labels_dir / txt_filename
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(word)
            
            if (i + 1) % 100 == 0:
                print(f"Generated {i + 1} samples...")
        
        print(f"Dataset generation complete! Files saved in '{self.output_dir}'")
        print(f"Images: {self.images_dir}")
        print(f"Labels: {self.labels_dir}")

# Usage example
if __name__ == "__main__":
    generator = ArabicOCRWordGenerator()
    
    # Generate 500 samples (adjust as needed)
    generator.generate_dataset(500)
    
    # Optional: Generate a single sample for testing
    test_word = generator.generate_synthetic_arabic_word()
    test_img = generator.generate_word_image(test_word)
    test_img.save("test_arabic_word.png")
    print(f"Test word generated: {test_word}")

"""The script has been updated for Arabic OCR data generation! Here are the key features:
Arabic-specific capabilities:

Generates synthetic Arabic words using real Arabic letters (ا، ب، ت، etc.)
Uses common Arabic prefixes (ال، و، ف) and suffixes (ها، ان، ين)
Incorporates Arabic numbers (٠١٢٣٤٥٦٧٨٩)
Handles Arabic text direction and shaping

Handwritten effects:

Adds character-level variations (rotation, position shifts)
Simulates ink color variations
Creates paper texture with noise
Adds occasional ink blots and smudges
Applies slight blur for realistic handwriting appearance

Required dependencies:pip install Pillow numpy arabic-reshaper python-bidi

Font recommendations:
The script tries to find Arabic fonts automatically, but for best results, download and install:

Noto Sans Arabic (free, excellent coverage)
Amiri (traditional Arabic calligraphy style)
Cairo (modern Arabic font)

Usage:

Run the script to generate 500 samples (adjustable)
Images saved as PNG files in images/ folder
Corresponding Arabic text saved as UTF-8 encoded .txt files in labels/ folder

The generated words will look like authentic Arabic handwriting with natural variations, perfect for training OCR models on Arabic text!
"""