import base64
import json
from pathlib import Path
from typing import AsyncGenerator, Generator

import cv2
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
                logger.error(f"无法访问 PDF 文件 {file_path}: {e}")


def gen_pdf_pages(pdf_path: Path) -> Generator[fitz.Page, None, None]:
    """
    生成 PDF 文档中的每一页。

    Args:
        pdf_path (Path): pdf_path (Path): PDF 文件路径。

    Returns:
        Generator[fitz.Page, None, None]: PDF 的单页对象的生成器。

    Yields:
        Iterator[Generator[fitz.Page, None, None]]: PDF 的单页对象可迭代对象。
    """

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        logger.error(f"无法打开 PDF 文件: {e}")

    for page_number in range(len(doc)):
        yield doc.load_page(page_number)


def page_to_pixmap(
    page: fitz.Page, scale: float = 1.25, gray: bool = True
) -> fitz.Pixmap:
    """
    将 PDF 页面对象渲染为图像 Pixmap。

    Args:
        page (fitz.Page): PDF 页面对象。
        scale (float): 渲染缩放比例。
        gray (bool): 是否使用灰度图。

    Returns:
        fitz.Pixmap: 渲染后的图像。
    """
    matrix = fitz.Matrix(scale, scale)
    colorspace = fitz.csGRAY if gray else fitz.csRGB
    return page.get_pixmap(matrix=matrix, colorspace=colorspace, alpha=False)


def pixmap_to_base64(pix: fitz.Pixmap) -> str:
    """
    将 fitz.Pixmap 转换为 base64 编码的 PNG 图像（不带 data URL 前缀）。

    Args:
        pix (fitz.Pixmap): 待转换的 fitz.Pixmap 对象。

    Raises:
        ValueError: 如果 PNG 编码失败。

    Returns:
        str: base64 编码的 PNG 图像字符串。
    """
    image: np.ndarray = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
        pix.height, pix.width, pix.n
    )

    # 通道处理
    if pix.n == 1:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    elif pix.n == 4:
        image = image[:, :, :3]

    success, png_data = cv2.imencode(".png", image)
    if not success:
        raise ValueError("PNG 编码失败")

    return base64.b64encode(png_data.tobytes()).decode("utf-8")


def make_data_url(base64_str: str, mime_type: str = "image/png") -> str:
    """
    将 base64 字符串组装为 data URL 格式。

    Args:
        base64_str (str): base64 编码内容。
        mime_type (str): MIME 类型，默认使用 PNG。

    Returns:
        str: 完整的 data URL 字符串。
    """
    return f"data:{mime_type};base64,{base64_str}"


def make_vision_jsonl_line(
    image_data_url: str,
    prompt: str,
    custom_id: str,
    model: str = "gpt-4o-mini",
    detail: str = "auto",
) -> dict:
    """
    构造一个符合 OpenAI Batch API 视觉模型格式的 JSONL 请求行。

    Args:
        image_data_url (str): 图像的 data URL 字符串（Base64 编码）。
        prompt (str): 用户输入的文字 prompt。
        custom_id (str): 当前请求的唯一标识。
        model (str, optional): 模型名称，默认使用 gpt-4o-mini。
        detail (str, optional): 图像 detail 设置（low / high / auto），默认使用 low 以节省 token。

    Returns:
        dict: 可写入 JSONL 文件的一行请求结构。
    """
    return {
        "custom_id": custom_id,
        "method": "POST",
        "url": "/v1/responses",
        "body": {
            "model": model,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {
                            "type": "input_image",
                            "image_url": image_data_url,
                            "detail": detail,
                        },
                    ],
                }
            ],
        },
    }


def generate_jsonl_lines_from_pdf(
    pdf_path: Path,
    prompt: str,
    model: str = "gpt-4o-mini",
    detail: str = "auto",
) -> Generator[dict, None, None]:
    """
    给定一个 PDF 文件路径，逐页生成符合 OpenAI Batch API JSONL 格式的请求行。

    Args:
        pdf_path (Path): PDF 文件路径。
        prompt (str): 用户输入的文字 prompt。
        model (str, optional): 具体模型 Defaults to "gpt-4o-mini".
        detail (str, optional): 需要模型了解的细节程度 Defaults to "auto".

    Yields:
        Generator[dict, None, None]: 符合 OpenAI Batch API JSONL 格式的请求行。
    """
    for idx, page in enumerate(gen_pdf_pages(pdf_path)):
        pix = page_to_pixmap(page)
        base64_img = pixmap_to_base64(pix)
        data_url = make_data_url(base64_img)
        custom_id = f"{pdf_path.stem}-page-{idx + 1:04d}"
        yield make_vision_jsonl_line(
            image_data_url=data_url,
            prompt=prompt,
            custom_id=custom_id,
            model=model,
            detail=detail,
        )


def write_jsonl_append(
    file_path: Path, jsonl_generator: Generator[dict, None, None]
) -> None:
    """
    将 JSONL 数据追加到指定文件中。

    Args:
        file_path (Path): 要写入的文件路径。
        jsonl_generator (Generator[dict, None, None]): JSONL 数据生成器。
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("a", encoding="utf-8") as f:
        for item in jsonl_generator:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
