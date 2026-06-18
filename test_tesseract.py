import cv2
import pytesseract

# IMPORTANT:
# Verify this path on the new PC
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

image_path = "sample.png"

img = cv2.imread(image_path)

if img is None:
    print("Image not found!")
    exit()

# Convert to grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Upscale image for better OCR
gray = cv2.resize(
    gray,
    None,
    fx=2,
    fy=2,
    interpolation=cv2.INTER_CUBIC
)

# Threshold
_, thresh = cv2.threshold(
    gray,
    150,
    255,
    cv2.THRESH_BINARY
)

# OCR
text = pytesseract.image_to_string(
    thresh,
    config="--psm 6"
)

print("\n===== OCR OUTPUT =====\n")
print(text)
print("\n======================\n")