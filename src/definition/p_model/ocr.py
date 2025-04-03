from typing import Generator, List

from pydantic import BaseModel, Field


class BBoxPoint(BaseModel):
    """
    表示 OCR 检测框中的一个二维点坐标。

    Attributes:
        x (int): X 坐标。
        y (int): Y 坐标。
    """

    x: int = Field(..., description="坐标 x")
    y: int = Field(..., description="坐标 y")


class OCRBox(BaseModel):
    """
    表示 OCR 识别出的单个文本块，包括其位置、内容和置信度。

    Attributes:
        box (List[BBoxPoint]): 文本块的四边形坐标点（顺时针顺序）。
        text (str): 识别出的文字内容。
        score (float): 识别的置信度，取值范围为 0.0 到 1.0。
    """

    box: List[BBoxPoint] = Field(..., description="四个点的边框，顺时针排列")
    text: str = Field(..., description="识别出的文本内容")
    score: float = Field(..., ge=0.0, le=1.0, description="置信度，范围在 0 ~ 1 之间")


class OCRPageResult(BaseModel):
    """
    表示单页 PDF 图像的 OCR 识别结果，包含该页中所有识别出的文本块。

    Attributes:
        results (List[OCRBox]): 当前页面中的所有文本识别结果。
    """

    results: List[OCRBox] = Field(..., description="当前页面中的所有文本识别结果")

    @property
    def boxes(self) -> List[OCRBox]:
        """
        访问器，返回当前页面中的所有文本识别结果。

        Returns:
            List[OCRBox]: 将 OCR 结果作为可重复访问的列表返回。
        """
        return self.results

    def gen_boxes(self) -> Generator[OCRBox, None, None]:
        """
        生成器，逐个返回当前页面中的所有文本识别结果。

        Yields:
            OCRBox: 当前页面中的每个文本块的识别结果。
        """
        for box in self.results:
            yield box
