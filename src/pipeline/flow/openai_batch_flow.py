from pathlib import Path

from src.pipeline.task.openai_batch import (
    create_batch,
    download_batch_output,
    upload_batch_file,
    wait_for_batch,
)


def openai_batch_flow(jsonl_path: Path) -> None:
    """
    执行一键式完整 Batch 请求流程。

    Args:
        jsonl_path (str): 输入 JSONL 文件路径。
    """
    file_id = upload_batch_file(jsonl_path)
    batch_id = create_batch(file_id)
    output_file_id = wait_for_batch(batch_id)
    if output_file_id:
        download_batch_output(output_file_id)
