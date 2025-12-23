"""
浏览器适配器接口

定义浏览器操作的抽象契约。
"""

from typing import Protocol, List, Any, Optional


class IBrowserAdapter(Protocol):
    """
    浏览器适配器接口
    
    职责:
    - 提供浏览器操作的统一抽象
    - 隔离具体浏览器实现（DrissionPage等）
    """
    
    def get_current_tab(self) -> Any:
        """获取当前标签页"""
        ...
    
    def get_tab_by_id(self, tab_id: str) -> Optional[Any]:
        """根据ID获取标签页"""
        ...
    
    def list_tabs(self) -> List[dict]:
        """列出所有标签页"""
        ...
    
    def run_js(self, tab: Any, script: str) -> Any:
        """执行 JavaScript"""
        ...
    
    def find_element(self, tab: Any, selector: str, timeout: float = 3.0) -> Optional[Any]:
        """查找元素"""
        ...
    
    def click_element(self, tab: Any, element: Any) -> bool:
        """点击元素"""
        ...
    
    def fill_input(self, tab: Any, element: Any, value: str) -> bool:
        """填充输入框"""
        ...
