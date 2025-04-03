from loguru import logger

from src.definition.const.location import LOG_DIR


def configure_logging() -> None:
    """
    配置日志：移除默认输出，添加文件日志，日志格式包含文件位置和行号，
    日志信息换行输出，每天生成一个日志文件，旧日志压缩并保留一周。
    """
    # 移除默认的输出
    logger.remove()

    # 添加文件日志，不输出到控制台
    logger.add(
        LOG_DIR / "app.log",
        level="DEBUG",
        rotation="1 day",  # 每天一个日志文件
        retention="1 week",  # 保留一周的日志文件
        compression="zip",  # 旧日志自动压缩
        format=("{time:YYYY-MM-DD HH:mm:ss} | {level} | {file}:{line}\n{message}\n"),
        encoding="utf-8",
        enqueue=True,
    )
