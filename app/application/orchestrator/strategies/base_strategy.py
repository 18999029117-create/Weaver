"""
填充策略基类

定义填充策略的接口，供各具体策略实现。
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Callable, Dict

# 避免循环导入，使用 TYPE_CHECKING
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.application.orchestrator.fill_session_controller import FillSessionController


class BaseFillStrategy(ABC):
    """
    填充策略基类
    
    定义通用接口和辅助方法。
    """
    
    def __init__(self, controller: 'FillSessionController'):
        """
        初始化策略
        
        Args:
            controller: FillSessionController 实例，用于访问状态和配置
        """
        self.controller = controller
    
    @property
    def tab(self):
        """浏览器标签页"""
        return self.controller.tab
    
    @property
    def state(self):
        """会话状态"""
        return self.controller.state
    
    @property
    def config(self):
        """会话配置"""
        return self.controller.config
    
    @property
    def field_mapping(self):
        """字段映射"""
        return self.controller.field_mapping
    
    @property
    def excel_data(self):
        """Excel 数据"""
        return self.controller.excel_data
    
    @property
    def abort_event(self):
        """中止事件"""
        return self.controller.abort_event
    
    @property
    def pagination_controller(self):
        """翻页控制器"""
        return self.controller.pagination_controller
    
    def _log(self, message: str, level: str = "info"):
        """日志输出"""
        self.controller._log(message, level)
    
    def _progress(self, current: int, total: int, page: int):
        """进度更新"""
        self.controller._progress(current, total, page)
    
    def _complete_fill(self):
        """完成填充"""
        self.controller._complete_fill()
    
    @abstractmethod
    def execute(self) -> None:
        """
        执行填充策略
        
        各策略必须实现此方法。
        """
        pass
    
    @abstractmethod
    def continue_fill(self) -> None:
        """
        继续填充（翻页后或暂停恢复后）
        
        各策略必须实现此方法。
        """
        pass
