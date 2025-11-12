import numpy as np
import cv2

def preprocess(img, image_width=128, image_height=32, augment=False):
    """
    Preprocess image: resize, transpose, normalize
    """

    if augment:
        stretch = (np.random.rand() - 0.5)  # -0.5 .. +0.5
        wStretched = max(int(img.shape[1] * (1 + stretch)), 1)
        img = cv2.resize(img, (wStretched, img.shape[0]))

    # Resize image to fit target size
    (h, w) = img.shape
    fx = w / image_width
    fy = h / image_height
    f = max(fx, fy)
    new_size = (max(min(image_width, int(w / f)), 1),
                max(min(image_height, int(h / f)), 1))
    img = cv2.resize(img, new_size)

    # Place resized image into white canvas
    target = np.ones([image_height, image_width]) * 255
    target[0:new_size[1], 0:new_size[0]] = img

    # Transpose for model input
    img = cv2.transpose(target)

    # Normalize
    (m, s) = cv2.meanStdDev(img)
    img = img - m[0][0]
    img = img / s[0][0] if s[0][0] > 0 else img

    return img
