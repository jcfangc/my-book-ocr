import time
from pathlib import Path
from typing import Optional

from loguru import logger

from src.definition.const.core import CLIENT
from src.definition.const.location import OUTPUT_DIR


def upload_batch_file(file_path: Path) -> str:
    """
    上传 JSONL 批处理输入文件到 OpenAI。

    Args:
        file_path (Path): 要上传的文件路径。

    Returns:
        str: 上传成功后的 file_id。
    """
    with file_path.open("rb") as f:
        file = CLIENT.files.create(file=f, purpose="batch")
    logger.info(f"[上传成功] file_id: {file.id}")
    return file.id


def create_batch(
    file_id: str, endpoint: str = "/v1/responses", window: str = "24h"
) -> str:
    """
    使用上传的文件创建 Batch 请求。

    Args:
        file_id (str): 输入文件的 file_id。
        endpoint (str): 调用的 OpenAI API endpoint。
        window (str): 完成时间窗口（目前仅支持 24h）。

    Returns:
        str: batch_id
    """
    batch = CLIENT.batches.create(
        input_file_id=file_id,
        endpoint=endpoint,
        completion_window=window,
        metadata={"description": "Markdown OCR Batch Job"},
    )
    logger.info(f"[创建成功] batch_id: {batch.id}")
    return batch.id


def wait_for_batch(batch_id: str, interval: int = 10) -> Optional[str]:
    """
    轮询等待 batch 执行完成。

    Args:
        batch_id (str): 批处理任务 ID。
        interval (int): 轮询间隔时间（秒）。

    Returns:
        Optional[str]: 输出文件的 file_id，如果失败则为 None。
    """
    logger.info(f"[等待中] batch_id: {batch_id}")
    while True:
        batch = CLIENT.batches.retrieve(batch_id)
        status = batch.status
        logger.info(f"当前状态: {status}")
        if status == "completed":
            logger.info("[完成] 任务已完成")
            return batch.output_file_id
        elif status in {"failed", "expired", "cancelled"}:
            logger.info(f"[失败] 批处理失败，状态: {status}")
            return None
        time.sleep(interval)


def download_batch_output(
    output_file_id: str, save_path: Path = OUTPUT_DIR / "ocr.jsonl"
) -> None:
    """
    下载批处理的输出结果。

    Args:
        output_file_id (str): OpenAI 返回的输出文件 ID。
        save_path (Path): 保存文件路径。
    """
    # 确保输出目录存在
    save_path.parent.mkdir(parents=True, exist_ok=True)

    # 下载文件内容
    content = CLIENT.files.content(output_file_id)
    save_path.write_text(content.text, encoding="utf-8")

    logger.info(f"[保存成功] 结果已保存到 {save_path}")
