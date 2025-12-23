"""
填充服务

封装表单填充的业务逻辑。
"""

from typing import Dict, Any, Optional, Callable

from app.domain.entities import ElementFingerprint
from app.core.smart_form_filler import SmartFormFiller


class FillingService:
    """
    填充服务
    
    职责:
    - 填充单个元素
    - 填充整个表单
    - 提供自愈能力
    """
    
    def __init__(self, tab: Any):
        """
        初始化填充服务
        
        Args:
            tab: 浏览器标签页对象
        """
        self.tab = tab
    
    def fill_element(self, fingerprint: ElementFingerprint, value: str) -> bool:
        """
        填充单个元素
        
        Args:
            fingerprint: 元素指纹
            value: 填充值
            
        Returns:
            是否成功
        """
        return SmartFormFiller._fill_with_fallback(self.tab, fingerprint, value)
    
    def fill_form(
        self,
        excel_data: Any,  # pandas DataFrame
        mappings: Dict[str, ElementFingerprint],
        fill_mode: str = 'single_form',
        key_column: Optional[str] = None,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        填充整个表单
        
        Args:
            excel_data: Excel 数据
            mappings: 字段映射
            fill_mode: 填充模式
            key_column: 锚点列
            progress_callback: 进度回调
            
        Returns:
            填充结果统计
        """
        return SmartFormFiller.fill_form_with_healing(
            tab=self.tab,
            excel_data=excel_data,
            fingerprint_mappings=mappings,
            fill_mode=fill_mode,
            key_column=key_column,
            progress_callback=progress_callback
        )
