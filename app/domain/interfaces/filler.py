"""
表单填充器接口

定义表单填充的抽象契约。
"""

from typing import Protocol, Dict, Any, Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ..entities import ElementFingerprint
    import pandas as pd


class IFormFiller(Protocol):
    """
    表单填充器接口
    
    职责:
    - 填充表单元素
    - 支持多种填充模式
    - 提供自愈能力
    """
    
    def fill_element(
        self, 
        tab: Any, 
        fingerprint: 'ElementFingerprint', 
        value: str
    ) -> bool:
        """
        填充单个元素
        
        Args:
            tab: 浏览器标签页对象
            fingerprint: 元素指纹
            value: 填充值
            
        Returns:
            是否成功
        """
        ...
    
    def fill_form(
        self,
        tab: Any,
        excel_data: 'pd.DataFrame',
        mappings: Dict[str, 'ElementFingerprint'],
        fill_mode: str = 'single_form',
        key_column: Optional[str] = None,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        填充整个表单
        
        Args:
            tab: 浏览器标签页对象
            excel_data: Excel 数据
            mappings: 字段映射关系
            fill_mode: 填充模式
            key_column: 锚定列
            progress_callback: 进度回调
            
        Returns:
            填充结果统计
        """
        ...
