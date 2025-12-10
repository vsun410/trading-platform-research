"""로거 설정"""

import sys
from loguru import logger


def setup_logger(
    level: str = "INFO",
    log_file: str = None,
    rotation: str = "10 MB"
) -> None:
    """
    로거 설정
    
    Args:
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR)
        log_file: 로그 파일 경로 (None이면 콘솔만)
        rotation: 로그 파일 회전 크기
    """
    # 기존 핸들러 제거
    logger.remove()
    
    # 콘솔 출력
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # 파일 출력
    if log_file:
        logger.add(
            log_file,
            level=level,
            rotation=rotation,
            retention="7 days",
            compression="gz"
        )
