import io
import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from PIL import Image
from dotenv import load_dotenv
load_dotenv()
# Initialize the modern, fast SDK client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class ExtractedStampData(BaseModel):
    certificate_number: str = Field(description="The unique e-stamp identification number.")
    stamp_duty_amount: int = Field(description="The face value amount in INR.")

def analyze_stamp_screenshot(image_bytes: bytes) -> ExtractedStampData:
    """
    Optimized low-latency vision pipeline for sub-2-second data processing.
    """
    # --- Optimization 1: Network Image Compression ---
    # Open image, convert to standard RGB, resize down if massive, and save with high compression
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    
    # Target maximum dimensions to save network bandwidth while preserving crisp text readability
    img.thumbnail((1024, 1024)) 
    
    compressed_buffer = io.BytesIO()
    img.save(compressed_buffer, format="JPEG", quality=75,optimize=True) # 75% quality dramatically slashes file size
    compressed_bytes = compressed_buffer.getvalue()
    
    # Structure the compressed bytes into the payload format the SDK prefers
    image_part = types.Part.from_bytes(
        data=compressed_bytes,
        mime_type="image/jpeg",
    )

    # --- Optimization 2: Stripped-down Hyper-focused Prompt ---
    prompt = "Return JSON matching schema. Extract Certificate Number and Stamp Duty Amount."

    try:
        # --- Optimization 3: Lite Model + Bypassing Thinking Overhead ---
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',  # Swapped to ultra-low latency model
            contents=[image_part, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ExtractedStampData,
                temperature=0.0,  # 0.0 eliminates creativity for maximum consistency
                # Removes reasoning thinking loops entirely to save precious seconds
                thinking_config=types.ThinkingConfig(thinking_budget=0) 
            ),
        )
        
        return ExtractedStampData.model_validate_json(response.text)

    except Exception as e:
        raise ValueError(f"Speed OCR Pipeline Failed: {str(e)}")