import io
from pathlib import Path
from PIL import Image
import pytesseract
from app.path_ai.core.config import settings
from app.path_ai.monitoring.logger import get_logger

logger = get_logger(__name__)

# Set Tesseract path from config
if hasattr(settings, 'tesseract_cmd') and settings.tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

def ocr_image(image_bytes: bytes) -> str:
    try:
        img = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(img, lang="ind+eng")
        return text.strip()
    except Exception as e:
        logger.warning("OCR failed for image", error=str(e))
        return ""

def ocr_image_from_path(image_path: str) -> str:
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang="ind+eng")
        return text.strip()
    except Exception as e:
        logger.warning("OCR failed", path=image_path, error=str(e))
        return ""

def process_images(images: list[bytes]) -> str:
    results = []
    for i, img_bytes in enumerate(images):
        text = ocr_image(img_bytes)
        if text:
            results.append(f"[Image {i+1}]\n{text}")
            logger.info(f"OCR extracted text from image {i+1}", chars=len(text))
    return "\n\n".join(results)
