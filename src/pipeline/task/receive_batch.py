import json
from datetime import datetime
from pathlib import Path

from loguru import logger

from src.definition.const.core import CLIENT
from src.definition.const.location import OUTPUT_DIR
from src.pipeline.task.openai_batch import download_batch_output


def list_recent_batches(limit: int = 10):
    """
    列出最近的 batch 批处理任务信息。
    """
    batches = CLIENT.batches.list(limit=limit)
    for batch in batches.data:
        created = datetime.fromtimestamp(batch.created_at).strftime("%Y-%m-%d %H:%M:%S")
        logger.info(
            f"🆔 batch_id: {batch.id} | 状态: {batch.status} | 创建时间: {created} | 请求数: {batch.request_counts.total}"
        )


def fetch_output_from_existing_batch(
    batch_id: str, save_path: Path = OUTPUT_DIR / "ocr.jsonl"
) -> None:
    """
    使用 batch_id 获取已完成批次的输出文件，并保存到指定路径。
    """
    batch = CLIENT.batches.retrieve(batch_id)
    if batch.status != "completed":
        raise RuntimeError(
            f"批次状态尚未完成（当前状态: {batch.status}），无法下载输出。"
        )
    output_file_id = batch.output_file_id
    download_batch_output(output_file_id, save_path)


def decode_openai_jsonl(input_path: Path, output_path: Path) -> None:
    """
    将 OpenAI Batch JSONL 输出文件转换为纯文本 Markdown。
    """

    if not input_path.exists():
        raise FileNotFoundError(f"输入文件 {input_path} 不存在。")
    if not input_path.is_file():
        raise ValueError(f"输入路径 {input_path} 不是一个文件。")
    if output_path.exists() and not output_path.is_file():
        raise ValueError(f"输出路径 {output_path} 不是一个文件。")
    if output_path.exists():
        logger.warning(f"输出文件 {output_path} 已存在，将被覆盖。")

    # 创建输出目录
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8") as f_in, output_path.open(
        "w", encoding="utf-8"
    ) as f_out:
        for line in f_in:
            record: dict = json.loads(line)  # 自动处理转义
            custom_id = record.get("custom_id", "unknown")

            text_blocks = []
            for message in record.get("response", {}).get("body", {}).get("output", []):
                if message.get("type") == "message":
                    for chunk in message.get("content", []):
                        if chunk.get("type") == "output_text":
                            text_blocks.append(chunk.get("text", ""))
            markdown_text = "\n".join(text_blocks)

            f_out.write(f"<!-- {custom_id} -->\n")
            f_out.write(markdown_text + "\n\n")

    print(f"✅ 已保存 Markdown 文本至 {output_path}")


if __name__ == "__main__":
    # # 示例：列出最近的 5 个批处理任务
    # list_recent_batches(limit=5)

    # # 示例：下载指定 batch_id 的输出文件
    # batch_id = "batch_67f1a3b93b588190809e50f5a4910ef9"

    # fetch_output_from_existing_batch(batch_id)
    # 示例：将 OpenAI Batch JSONL 输出转换为 Markdown 文本
    input_path = OUTPUT_DIR / "ocr.jsonl"
    output_path = OUTPUT_DIR / "ocr.md"
    decode_openai_jsonl(input_path, output_path)
