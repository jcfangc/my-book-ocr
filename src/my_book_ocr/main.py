from loguru import logger

from src.log.config import configure_logging
from src.pipeline.flow.pdf_to_md import pdf_to_md_batch_async

if __name__ == "__main__":
    configure_logging()

    logger.info("开始处理 PDF 文件...")

    pdf_to_md_batch_async()
