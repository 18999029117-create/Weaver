"""
表单分析器接口

定义表单扫描和分析的抽象契约。
"""

from typing import Protocol, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..entities import ElementFingerprint


class IFormAnalyzer(Protocol):
    """
    表单分析器接口
    
    职责:
    - 扫描页面中的可交互元素
    - 返回元素指纹列表
    """
    
    def scan_page(self, tab: Any, timeout: float = 10.0) -> List['ElementFingerprint']:
        """
        扫描页面元素
        
        Args:
            tab: 浏览器标签页对象
            timeout: 超时时间（秒）
            
        Returns:
            ElementFingerprint 列表
        """
        ...
    
    def scan_iframes(self, tab: Any) -> List['ElementFingerprint']:
        """
        扫描 Iframe 内元素
        
        Args:
            tab: 浏览器标签页对象
            
        Returns:
            ElementFingerprint 列表
        """
        ...
