"""
Weaver 日志系统

提供统一的日志接口，支持:
- 标准 Python logging 模块
- UI 回调日志（同步显示到界面）
- 文件日志输出

用法:
    from app.utils.logger import get_logger, setup_logging
    
    # 初始化日志系统（应用启动时调用）
    setup_logging()
    
    # 获取模块日志器
    logger = get_logger(__name__)
    logger.info("操作成功")
    logger.warning("警告信息")
    logger.error("错误信息")
    
    # 带 UI 回调的日志
    ui_logger = get_logger(__name__, ui_callback=my_callback)
    ui_logger.success("填充完成")
"""

import logging
import sys
from typing import Optional, Callable, Literal
from pathlib import Path
from datetime import datetime


# 日志级别类型
LogLevel = Literal["debug", "info", "success", "warning", "error", "critical"]

# 日志格式
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
SIMPLE_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
TIME_FORMAT = "%H:%M:%S"


class WeaverLogger:
    """
    Weaver 日志封装
    
    在标准 logging 基础上增加:
    - UI 回调支持
    - success 级别（介于 info 和 warning 之间）
    - 简化的 API
    """
    
    # 自定义 success 级别（25，介于 INFO=20 和 WARNING=30 之间）
    SUCCESS_LEVEL = 25
    
    def __init__(self, name: str, ui_callback: Optional[Callable[[str, str], None]] = None):
        """
        初始化 Weaver 日志器
        
        Args:
            name: 日志器名称（通常为 __name__）
            ui_callback: UI 回调函数，签名: (message, level) -> None
        """
        self.logger = logging.getLogger(name)
        self.ui_callback = ui_callback
        
        # 注册 success 级别
        if not hasattr(logging, 'SUCCESS'):
            logging.addLevelName(self.SUCCESS_LEVEL, 'SUCCESS')
    
    def _log_and_callback(self, level: int, message: str, level_name: str):
        """记录日志并调用 UI 回调"""
        self.logger.log(level, message)
        if self.ui_callback:
            try:
                self.ui_callback(message, level_name)
            except Exception:
                pass  # UI 回调失败不影响日志记录
    
    def debug(self, message: str):
        """调试级别日志"""
        self._log_and_callback(logging.DEBUG, message, "debug")
    
    def info(self, message: str):
        """信息级别日志"""
        self._log_and_callback(logging.INFO, message, "info")
    
    def success(self, message: str):
        """成功级别日志（带 ✅ 前缀）"""
        self._log_and_callback(self.SUCCESS_LEVEL, f"✅ {message}", "success")
    
    def warning(self, message: str):
        """警告级别日志"""
        self._log_and_callback(logging.WARNING, message, "warning")
    
    def error(self, message: str):
        """错误级别日志"""
        self._log_and_callback(logging.ERROR, message, "error")
    
    def critical(self, message: str):
        """严重错误级别日志"""
        self._log_and_callback(logging.CRITICAL, message, "critical")
    
    def set_ui_callback(self, callback: Optional[Callable[[str, str], None]]):
        """设置或更新 UI 回调"""
        self.ui_callback = callback


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    format_string: str = DEFAULT_FORMAT
):
    """
    初始化日志系统
    
    Args:
        level: 日志级别
        log_file: 日志文件路径（可选）
        format_string: 日志格式
    """
    # 基础配置
    handlers = [logging.StreamHandler(sys.stdout)]
    
    # 文件日志
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    
    logging.basicConfig(
        level=level,
        format=format_string,
        datefmt=TIME_FORMAT,
        handlers=handlers,
        force=True
    )
    
    # 降低第三方库日志级别
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('selenium').setLevel(logging.WARNING)


def get_logger(
    name: str,
    ui_callback: Optional[Callable[[str, str], None]] = None
) -> WeaverLogger:
    """
    获取 Weaver 日志器
    
    Args:
        name: 日志器名称（通常为 __name__）
        ui_callback: UI 回调函数
        
    Returns:
        WeaverLogger 实例
    """
    return WeaverLogger(name, ui_callback)


# 便捷的默认日志器
_default_logger: Optional[WeaverLogger] = None


def log(message: str, level: LogLevel = "info"):
    """
    便捷的日志函数
    
    Args:
        message: 日志消息
        level: 日志级别
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = get_logger("weaver")
    
    log_method = getattr(_default_logger, level, _default_logger.info)
    log_method(message)
