import asyncio
from pathlib import Path

from loguru import logger

from src.definition.const.location import INPUT_DIR, OUTPUT_DIR
from src.pipeline.task.pdf_ocr import (
    cluster_level_by_height,
    detect_list_item,
    generate_markdown_elements,
    ocr_image,
)
from src.pipeline.task.pdf_reader import gen_pdf_pages, gen_pdf_path, render_pdf_page_cv


async def pdf_to_md_batch_async(
    input_dir: Path = INPUT_DIR, output_dir: Path = OUTPUT_DIR
) -> None:
    """
    异步批量处理目录中的所有 PDF 文件，将其转换为 Markdown 并写入指定目录。

    利用 gen_pdf_path 异步生成器遍历目录中的 PDF 文件，然后对每个文件调用同步的
    pdf_to_md_single() 函数（通过 run_in_executor 调用），达到复用逻辑的目的。

    Args:
        input_dir (Path): PDF 输入目录。
        output_dir (Path): Markdown 输出目录。
    """
    logger.info(f"开始异步批量处理目录: {input_dir}")

    if not input_dir.exists():
        logger.error(f"输入目录不存在：{input_dir}")
        return

    loop = asyncio.get_running_loop()

    async for pdf_path in gen_pdf_path(input_dir):
        # 生成相对于输入目录的相对路径，并将扩展名替换为 .md
        rel_path = pdf_path.relative_to(input_dir).with_suffix(".md")
        output_path = output_dir / rel_path

        logger.info(f"处理文件: {pdf_path}")

        # 在默认线程池中调用同步的 pdf_to_md_single 函数，避免阻塞事件循环
        await loop.run_in_executor(None, pdf_to_md_single, pdf_path, output_path)

    logger.success("全部 PDF 异步处理完成。")


def pdf_to_md_single(pdf_path: Path, output_path: Path) -> None:
    """
    将一个 PDF 文件转为 Markdown 格式，并输出到指定目录（追加式写入）。

    Args:
        pdf_path (Path): 输入的 PDF 文件路径。
        output_dir (Path, optional): Markdown 文件输出目录，最终文件名将与 PDF 同名。
    """
    logger.info(f"开始处理 PDF: {pdf_path.name}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        logger.warning(f"输出文件 {output_path} 已存在，跳过处理。")
        return

    try:
        with output_path.open("w", encoding="utf-8") as f:
            for page_idx, page in enumerate(gen_pdf_pages(pdf_path)):
                image = render_pdf_page_cv(page)
                ocr_result = ocr_image(image)

                if not ocr_result.boxes:
                    logger.warning(f"第 {page_idx + 1} 页无识别内容，跳过。")
                    continue

                levels = cluster_level_by_height(ocr_result)
                styles = detect_list_item(ocr_result)
                elements = generate_markdown_elements(ocr_result, levels, styles)

                for element in elements:
                    f.write(element.render() + "\n\n")  # 追加写入每一行
    except Exception as e:
        logger.error(f"处理 PDF {pdf_path.name} 时出错：{e}")
        return

    logger.success(f"完成 Markdown 文件写入：{output_path}")
