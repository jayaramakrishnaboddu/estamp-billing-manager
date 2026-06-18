import io
import re
import pytesseract
from PIL import Image, ImageOps
from pydantic import BaseModel, Field
from typing import Optional

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

class ExtractedStampData(BaseModel):
    certificate_number: str = Field(
        description="The unique e-stamp identification number."
    )
    # Changed from stamp_duty back to stamp_duty_amount to resolve the 500 error
    stamp_duty_amount: int = Field(
        description="The face value amount in INR."
    )
    payment_mode: str = Field(
        description="The selected payment method mode."
    )
    customer_id: Optional[str] = None
    processed_by: Optional[str] = None


def analyze_stamp_screenshot(image_bytes: bytes) -> ExtractedStampData:
    # Load image from bytes
    img = Image.open(io.BytesIO(image_bytes))

    # Clean preprocessing optimized for clean data snippets
    gray = ImageOps.grayscale(img)
    resized = gray.resize((gray.width * 2, gray.height * 2), Image.Resampling.LANCZOS)
    thresh = resized.point(lambda p: 255 if p > 150 else 0)
    
    # Mode 6 forces structured line-by-line text blocks
    text = pytesseract.image_to_string(thresh, config="--psm 6")

    certificate_number = ""
    stamp_amount = 0
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    # 1. Extract Certificate Number (Find first instance containing 'IN-')
    for line in lines:
        upper_line = line.upper()
        # Handle common Tesseract replacements for 'I' like '|' or '§'
        if "IN-" in upper_line or "§N-" in upper_line or "|N-" in upper_line:
            # Match 'IN-' followed by alphanumeric sequence
            match_cert = re.search(r'([I§|]N-[\s\w\d]+)', upper_line)
            if match_cert:
                certificate_number = (
                    match_cert.group(1)
                    .replace("§", "I")
                    .replace("|", "I")
                    .replace(" ", "")
                    .replace(".", "")
                )
                break

    # 2. Extract Stamp Duty Amount (Find the last valid line containing digits)
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i]
        # Look for the first digits appearing right after the colon indicator
        match_amount = re.search(r'(?<=:)\s*(\d+)', line)
        if match_amount:
            value = int(match_amount.group(1))
            if value < 100000:
                stamp_amount = value
                break

    return ExtractedStampData(
        certificate_number=certificate_number,
        stamp_duty_amount=stamp_amount, # Assigned back to matching schema key
        payment_mode="Cash",
        customer_id=None,
        processed_by=None
    )
