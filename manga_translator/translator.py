import os
import sys
import cv2
import torch
import numpy as np
import html
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO
from manga_ocr import MangaOcr
from google.cloud import translate_v2 as translate
from typing import List, Dict, Any

from .memory import TranslationMemory


def resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class MangaTranslator:
    def __init__(self, google_api_key_path: str, yolo_model_path="yolo_models/yolov8m.pt",
                 font_path="fonts/mangat.ttf"):
        if torch.cuda.is_available():
            self.device = "cuda"
        elif torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"

        self.google_api_key_path = resource_path(google_api_key_path)
        yolo_path = resource_path(yolo_model_path)
        ocr_path = resource_path("local_models/manga-ocr-base")
        self.font_path = resource_path(font_path)

        if not os.path.exists(self.google_api_key_path):
            raise FileNotFoundError(f"Google API Key file not found at: {self.google_api_key_path}")
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.google_api_key_path
        self.translate_client = translate.Client()

        self.yolo_model = YOLO(yolo_path).to(self.device)

        if os.path.exists(ocr_path):
            self.ocr_model = MangaOcr(ocr_path)
        else:
            self.ocr_model = MangaOcr()

        self.tm = TranslationMemory()
        self.default_font_size = 28

    def _detect_bubbles(self, image_path: str) -> List[List[int]]:
        results = self.yolo_model(image_path, conf=0.15, iou=0.7, agnostic_nms=True, max_det=50)
        if not results or not results[0].boxes:
            return []
        bboxes = results[0].boxes.xyxy.int().tolist()
        return bboxes

    def _translate_with_feedback(self, text: str) -> str:
        if not text.strip():
            return ""

        cached_translation = self.tm.lookup(text)
        if cached_translation:
            return cached_translation

        try:
            result = self.translate_client.translate(text, source_language='ja', target_language='en')
            cleaned_text = self._clean_text(result['translatedText'])
            self.tm.add_translation(text, cleaned_text)
            return cleaned_text
        except Exception as e:
            print(f"   ❌ Google Translate API Error: {e}")
            return "Translation Failed"

    def _ocr_and_translate(self, image: np.ndarray, bubbles: List[List[int]]) -> List[Dict[str, Any]]:
        translations = []
        for i, bbox in enumerate(bubbles):
            x1, y1, x2, y2 = bbox
            cropped_bubble = image[y1:y2, x1:x2]
            pil_image = Image.fromarray(cv2.cvtColor(cropped_bubble, cv2.COLOR_BGR2RGB))
            original_text = self.ocr_model(pil_image).strip()
            translated_text = self._translate_with_feedback(original_text)
            translations.append({
                "id": i, "bbox": bbox, "original_text": original_text, "translated_text": translated_text
            })
        return translations

    @staticmethod
    def _clean_text(text: str) -> str:
        return html.unescape(text)

    def _apply_translations(self, image: np.ndarray, translations: List[Dict[str, Any]]) -> np.ndarray:
        output_image = image.copy()

        for bubble in translations:
            x1, y1, x2, y2 = bubble['bbox']
            bubble_crop = output_image[y1:y2, x1:x2]
            gray_crop = cv2.cvtColor(bubble_crop, cv2.COLOR_BGR2GRAY)
            _, text_mask = cv2.threshold(gray_crop, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            kernel = np.ones((3, 3), np.uint8)
            dilated_mask = cv2.dilate(text_mask, kernel, iterations=2)
            full_mask = np.zeros(output_image.shape[:2], dtype=np.uint8)
            full_mask[y1:y2, x1:x2] = dilated_mask
            output_image = cv2.inpaint(output_image, full_mask, inpaintRadius=5, flags=cv2.INPAINT_NS)

        img_pil = Image.fromarray(cv2.cvtColor(output_image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)

        for bubble in translations:
            translated_text = self._clean_text(bubble.get("translated_text", ""))
            if not translated_text:
                continue

            x1, y1, x2, y2 = bubble['bbox']
            padding = 15
            bubble_w, bubble_h = (x2 - x1) - padding, (y2 - y1) - padding
            font_size = self.default_font_size + 2

            wrapped_text = ""
            while font_size > 8:
                font = ImageFont.truetype(self.font_path, font_size)
                wrapped_text = self._wrap_text(translated_text, font, bubble_w)
                text_bbox = draw.textbbox((0, 0), wrapped_text, font=font, align="center")
                text_w, text_h = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

                if text_w < bubble_w and text_h < bubble_h:
                    break
                font_size -= 1

            text_bbox = draw.textbbox((0, 0), wrapped_text, font=font, align="center")
            text_w, text_h = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
            text_x = x1 + ((x2 - x1) - text_w) // 2
            text_y = y1 + ((y2 - y1) - text_h) // 2
            draw.text((text_x, text_y), wrapped_text, font=font, fill="black", align="center")

        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    @staticmethod
    def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> str:
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            if font.getbbox(test_line)[2] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)
        return "\n".join(lines)

    def process_page(self, image_path: str, output_path: str):
        image = cv2.imread(image_path)
        if image is None:
            print(f"❌ Could not read image: {image_path}")
            return

        bubbles = self._detect_bubbles(image_path)
        if not bubbles:
            cv2.imwrite(output_path, image)
            return

        translations = self._ocr_and_translate(image, bubbles)
        final_image = self._apply_translations(image, translations)
        cv2.imwrite(output_path, final_image)

    def close(self):
        self.tm.close()