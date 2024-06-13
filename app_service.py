import dataclasses

import cv2
import easyocr
import numpy as np
from nestipy.common import Injectable, UploadFile
from ultralytics import YOLO

LICENSE_MODEL_DETECTION_DIR = './models/license_plate_detector.pt'
COCO_MODEL_DIR = "./models/yolov8n.pt"

coco_model = YOLO(COCO_MODEL_DIR)
license_plate_detector = YOLO(LICENSE_MODEL_DETECTION_DIR)

reader = easyocr.Reader(["en", "fr"])


@dataclasses.dataclass
class OcrDto:
    image: UploadFile


@Injectable()
class AppService:

    @classmethod
    async def get(cls):
        return "test"

    async def post(self, data: OcrDto):
        contents = await data.image.read(-1)
        img = cv2.imdecode(np.fromstring(contents, dtype=np.uint8, count=-1),cv2.IMREAD_COLOR)
        img_to_an = img.copy()
        license_detections = license_plate_detector(img_to_an)[0]
        data: list[tuple[str, float]] = []
        if len(license_detections.boxes.cls.tolist()) != 0:
            for license_plate in license_detections.boxes.data.tolist():
                x1, y1, x2, y2, score, class_id = license_plate
                cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 3)
                license_plate_crop = img[int(y1):int(y2), int(x1): int(x2), :]
                license_plate_crop_gray = cv2.cvtColor(license_plate_crop, cv2.COLOR_BGR2GRAY)
                license_plate_text, license_plate_text_score = self.read_license_plate(license_plate_crop_gray)
                if license_plate_text is not None and license_plate_text_score is not None:
                    data.append((license_plate_text, license_plate_text_score))

        if len(data) > 0:
            return {"ocr": data[0][0]}
        return {"ocr": ""}

    @classmethod
    async def put(cls, id_: int, data: dict):
        return "test"

    @classmethod
    async def delete(cls, id_: int):
        return "test"

    @classmethod
    def read_license_plate(cls, license_plate_crop) -> tuple[str | None, float | None]:
        detections = reader.readtext(license_plate_crop)
        if not detections:
            return None, None
        for detection in detections:
            bbox, text, score = detection
            text = text.upper()
            if text is not None and score is not None and bbox is not None and len(text) >= 6:
                return text, score
        return None, None
