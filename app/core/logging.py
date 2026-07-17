import sys

from loguru import logger

from app.core.config import settings


def setup_logging() -> None:
    logger.remove()

    log_format: str
    if settings.log_json:
        log_format = (
            '{"time":"{time:YYYY-MM-DDTHH:mm:ss.SSSZ}",'
            '"level":"{level}",'
            '"name":"{name}",'
            '"function":"{function}",'
            '"line":{line},'
            '"message":"{message}"}'
        )
    else:
        log_format = (
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level:<8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.log_level,
        colorize=not settings.log_json,
    )

    logger.info("Logging configured", level=settings.log_level, json_mode=settings.log_json)
