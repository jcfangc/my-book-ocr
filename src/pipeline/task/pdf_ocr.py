from typing import Generator, List

import numpy as np
from loguru import logger
from paddleocr import PaddleOCR
from sklearn.cluster import KMeans

from definition.p_model.ocr import (
    BBoxPoint,
    OCRBox,
    OCRPageResult,
)
from src.definition.const.core import LIST_PREFIX, OCR_MODEL
from src.definition.enum.markdown_syntax import MarkdownLevel, MarkdownStyle
from src.definition.p_model.md import MarkdownElement


def ocr_image(image: np.ndarray, ocr_model: PaddleOCR = OCR_MODEL) -> OCRPageResult:
    """
    对单张图像执行 OCR 推理，并将结果转换为结构化模型对象。

    Args:
        image (np.ndarray): 输入图像（RGB 格式）。
        ocr_model (PaddleOCR, optional): OCR 模型实例，默认为全局 OCR_MODEL。

    Returns:
        OCRPageResult: 当前图像的结构化 OCR 识别结果。
    """
    # 执行 OCR 推理
    result = ocr_model.ocr(image, cls=True)

    if not result:
        return OCRPageResult(results=[])

    structured_results = []
    for box_coords, (text, score) in result[0]:
        box = [BBoxPoint(x=int(pt[0]), y=int(pt[1])) for pt in box_coords]
        structured_results.append(OCRBox(box=box, text=text, score=score))

    return OCRPageResult(results=structured_results)


def cluster_level_by_height(
    page: OCRPageResult,
    n_levels: int = len(MarkdownLevel),
) -> List[MarkdownLevel]:
    """
    根据每个文本框的高度，对 OCR 文本块进行聚类，用于推测 Markdown 层级（标题/正文等）。

    使用 KMeans 对每个 OCRBox 的像素高度进行聚类，输出每个框对应的 MarkdownLevel 枚举值，
    MarkdownLevel 越靠前表示字号越大，结构层级越高。

    Args:
        page (OCRPageResult): OCR 识别结果页面，包含多个文本框（OCRBox）。
        n_levels (int, optional): 聚类层数，对应 Markdown 的层级数，默认等于 MarkdownLevel 枚举数量。

    Returns:
        List[MarkdownLevel]: 每个 OCRBox 的 Markdown 层级枚举值，顺序与 `page.gen_boxes()` 输出一致。
    """
    # 提取每个文本框的像素高度（上下点差值）
    heights = [
        max(p.y for p in box.box) - min(p.y for p in box.box) for box in page.boxes
    ]

    # 构造特征向量（二维数组），每个样本为一个高度值
    X = np.array(heights).reshape(-1, 1)

    # 进行 KMeans 聚类，将高度分为 n_levels 类
    labels = KMeans(n_clusters=n_levels, random_state=42).fit_predict(X)

    # --- 以下三行用于重新编号：确保 cluster label 0 对应最大字号（即 Markdown 层级最高） ---

    # 将 (原始聚类标签, 高度值) 打包为元组，并去重后按高度从高到低排序。
    # 目的是将“更大的字号”排在前面，从而编号为更高的 Markdown 层级。
    sorted_clusters = sorted(set(zip(labels, heights)), key=lambda x: -x[1])

    # 构建一个映射表：将原始标签（可能是 0,1,2,…）重新编号为 Markdown 层级编号（0 是最大字号）
    # 例如原始标签 1 对应最大高度，就将其映射为 0；原始标签 0 对应最小高度，就映射为 2
    mapping = {
        old_label: new_level for new_level, (old_label, _) in enumerate(sorted_clusters)
    }

    # 将原始标签按 mapping 映射为 MarkdownLevel 枚举值，并确保索引不会越界
    # 如果实际层级数 > MarkdownLevel 枚举数量，将多余层级都映射为最后一个 MarkdownLevel（通常是 PARAGRAPH）
    level_enum = list(MarkdownLevel)
    return [level_enum[min(mapping[label], len(level_enum) - 1)] for label in labels]


def detect_list_item(
    page: OCRPageResult, list_prefixes: List[str] = LIST_PREFIX
) -> List[MarkdownStyle]:
    """
    基于文本前缀，判断每一行是否为列表项，返回 MarkdownStyle 枚举值列表。

    Args:
        page (OCRPageResult): OCR 识别结果页面。
        list_prefixes (List[str], optional): 判断为列表项的前缀符号集合。

    Returns:
        List[MarkdownStyle]: 与 page.gen_boxes() 顺序一致的 Markdown 样式修饰结果。
    """
    return [
        MarkdownStyle.LIST_ITEM
        if box.text.strip().startswith(tuple(list_prefixes))
        else MarkdownStyle.NONE
        for box in page.boxes
    ]


def generate_markdown_elements(
    page: OCRPageResult,
    levels: List[MarkdownLevel],
    styles: List[MarkdownStyle],
) -> Generator[MarkdownElement, None, None]:
    """
    将 OCRPageResult + 层级标签 + 样式标签转换为 MarkdownElement 生成器。

    Args:
        page (OCRPageResult): OCR 识别结果页面。
        levels (List[MarkdownLevel]): 每个文本块对应的 Markdown 层级。
        styles (List[MarkdownStyle]): 每个文本块对应的 Markdown 样式修饰。

    Yields:
        Generator[MarkdownElement, None, None]: 结构化的 Markdown 元素。
    """
    if not len(page.boxes) == len(levels) == len(styles):
        logger.error("长度不一致：page.boxes, levels, styles 必须具有相同的长度")

    for box, level, style in zip(page.boxes, levels, styles):
        yield MarkdownElement(level=level, style=style, content=box.text.strip())
