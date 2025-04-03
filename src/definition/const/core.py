from paddleocr import PaddleOCR

OCR_MODEL = PaddleOCR(use_angle_cls=True, lang="ch_en")

LIST_PREFIX = ["-", "•", "·", "●"]
