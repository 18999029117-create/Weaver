"""
Filler 模块

提供表单填充功能，包括：
- ElementUIFiller: Element UI 专用填充器
- EventSimulator: 事件模拟填充器
- SmartFormFiller: 智能表单填充器（主入口）

使用示例:
    from app.core.filler import ElementUIFiller
    
    ElementUIFiller.fill_by_placeholder(tab, "请输入姓名", "张三")
"""

from typing import List, Dict, Any, Optional, Union, TYPE_CHECKING

from .element_ui_filler import ElementUIFiller
from .event_simulator import EventSimulator

if TYPE_CHECKING:
    from ..fingerprint import ElementFingerprint


class SmartFormFiller:
    """
    智能表单填充器 (Facade 门面类)
    
    提供统一的表单填充接口，整合多种填充策略。
    保持与原有代码的兼容性。
    """
    
    @staticmethod
    def fill_element_ui_input(
        tab,
        placeholder: str,
        value: Union[str, int, float],
        ensure_iframe: bool = True
    ) -> bool:
        """
        Element UI 输入框填充（自动处理 Iframe）
        
        Args:
            tab: DrissionPage 的 tab 对象
            placeholder: 输入框 placeholder
            value: 要填充的值
            ensure_iframe: 是否自动进入 Iframe
            
        Returns:
            填充是否成功
        """
        if ensure_iframe:
            return ElementUIFiller.fill_in_iframe(tab, placeholder, value)
        else:
            return ElementUIFiller.fill_by_placeholder(tab, placeholder, value)
    
    @staticmethod
    def fill_element_ui_by_label(
        tab,
        label_text: str,
        value: Union[str, int, float]
    ) -> bool:
        """
        通过 Element UI 标签文本填充
        
        Args:
            tab: DrissionPage 的 tab 对象
            label_text: 标签文本
            value: 要填充的值
            
        Returns:
            填充是否成功
        """
        return ElementUIFiller.fill_by_label(tab, label_text, value)
    
    @staticmethod
    def fill_with_js_events(
        tab,
        fingerprint: 'ElementFingerprint',
        value: Union[str, int, float]
    ) -> bool:
        """
        使用完整事件链填充元素
        
        Args:
            tab: DrissionPage 的 tab 对象
            fingerprint: 元素指纹
            value: 要填充的值
            
        Returns:
            填充是否成功
        """
        return EventSimulator.fill_with_events(
            tab,
            elem_id=fingerprint.selectors.get('id', ''),
            xpath=fingerprint.selectors.get('xpath', ''),
            css_selector=fingerprint.selectors.get('css', ''),
            value=str(value),
            elem_type=fingerprint.raw_data.get('type', 'text'),
            tag_name=fingerprint.raw_data.get('tagName', 'input')
        )


__all__ = [
    'SmartFormFiller',
    'ElementUIFiller',
    'EventSimulator',
]
