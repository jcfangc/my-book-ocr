from pathlib import Path
from typing import AsyncGenerator

import fitz
import numpy as np
from aiofile import async_open
from loguru import logger

from definition.const.location import INPUT_DIR


async def gen_pdf_path(input_dir: Path = INPUT_DIR) -> AsyncGenerator[Path, None]:
    """
    异步遍历目录，查找所有 PDF 文件，确认文件可打开后逐个返回其路径。

    Args:
        input_dir (Path): 待遍历的文件夹路径。

    Returns:
        AsyncGenerator[Path, None]: 所有可访问的 PDF 文件路径。

    Yields:
        Iterator[AsyncGenerator[Path, None]]: 所有可访问的 PDF 文件路径。
    """

    for file_path in input_dir.rglob("*.pdf"):
        if file_path.is_file():
            try:
                # 异步方式尝试打开文件，确保文件存在且可读
                async with async_open(file_path, mode="rb") as afp:
                    await afp.read(1)  # 读取1字节以确认文件非空/可访问
                yield file_path
            except Exception as e:
                print(f"无法异步访问 PDF 文件 {file_path}: {e}")


async def gen_pdf_pages(pdf_path: Path) -> AsyncGenerator[fitz.Page, None]:
    """
    异步生成 PDF 文档中的每一页。

    Args:
        pdf_path (Path): pdf_path (Path): PDF 文件路径。

    Returns:
        AsyncGenerator[fitz.Page, None]: PDF 的单页对象的生成器。

    Yields:
        Iterator[AsyncGenerator[fitz.Page, None]]: PDF 的单页对象可迭代对象。
    """

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        logger.error(f"无法打开 PDF 文件: {e}")

    for page_number in range(len(doc)):
        yield doc.load_page(page_number)


def render_pdf_page_cv(page: fitz.Page, scale: float = 2.0) -> np.ndarray:
    """
    将单页 PDF 渲染为 OpenCV 格式图像（np.ndarray）。

    Args:
        page (fitz.Page): 需要渲染的 PDF 页面对象。
        scale (float, optional): 缩放比例，默认放大 2 倍以提升图像清晰度。可用于提升 OCR 精度。

    Returns:
        np.ndarray: 渲染后的图像，格式为 OpenCV 标准的 HWC（高、宽、通道）布局，dtype 为 uint8。
                    通道顺序为 RGB（可使用 cv2.cvtColor 转为 BGR）。
    """
    # 渲染为 pixmap，alpha=False 表示不包含透明通道
    pix: fitz.Pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)

    # 将 pixmap 的样本数据转为 numpy 数组
    image: np.ndarray = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
        pix.height, pix.width, pix.n
    )

    return image  # RGB 格式，适合直接送入 PaddleOCR
