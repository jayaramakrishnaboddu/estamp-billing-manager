import io
from PIL import Image
import pytesseract
from pydantic import BaseModel, Field

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

class ExtractedStampData(BaseModel):
    certificate_number: str = Field(
        description="The unique e-stamp identification number."
    )
    stamp_duty_amount: int = Field(
        description="The face value amount in INR."
    )


def analyze_stamp_screenshot(image_bytes: bytes) -> ExtractedStampData:

    img = Image.open(io.BytesIO(image_bytes))

    text = pytesseract.image_to_string(img)

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    certificate_number = ""
    stamp_amount = 0

    # Extract Certificate Number
    for line in lines:

        upper_line = line.upper()

        if "IN-" in upper_line or "§N-" in upper_line:

            certificate_number = (
                upper_line
                .replace("§", "I")
                .replace("|", "I")
                .replace(" ", "")
                .replace(".", "")
            )

            break

    # Extract Stamp Duty Amount
    for i in range(len(lines) - 1, -1, -1):

        if lines[i].isdigit():

            value = int(lines[i])

            if value < 100000:
                stamp_amount = value
                break

    return ExtractedStampData(
        certificate_number=certificate_number,
        stamp_duty_amount=stamp_amount
    )