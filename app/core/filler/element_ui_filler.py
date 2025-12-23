"""
Element UI 专用填充器

针对 Element UI / Ant Design / iView 等 Vue 组件库的填充逻辑。
通过 JavaScript 注入设置值并触发 Vue 双向绑定事件。

主要功能:
- 通过 placeholder 定位并填充
- 通过 label 文本定位并填充
- 触发 Vue 事件链 (input -> change -> blur)
"""

from typing import Optional, Dict, Any, Union


class ElementUIFiller:
    """
    Element UI 专用表单填充器
    
    使用 JavaScript 注入方式填充 Element UI 输入框，
    并正确触发 Vue.js 的双向绑定事件。
    """
    
    @staticmethod
    def fill_by_placeholder(
        tab_or_frame, 
        placeholder: str, 
        value: Union[str, int, float]
    ) -> bool:
        """
        通过 placeholder 定位并填充 Element UI 输入框
        
        该方法会自动切换到 iframe（如果存在），使用 XPath 定位元素，
        并触发完整的 Vue 事件链确保双向绑定生效。
        
        Args:
            tab_or_frame: DrissionPage 的 tab 或 frame 对象
            placeholder: 输入框的 placeholder 文本
            value: 要填充的值
            
        Returns:
            填充是否成功
        """
        from ...utils.js_store import get_element_ui_fill_js
        
        try:
            js_code = get_element_ui_fill_js(placeholder, str(value))
            result = tab_or_frame.run_js(js_code)
            
            if isinstance(result, dict) and result.get('success'):
                print(f"   ✅ Element UI 填充成功: {placeholder} = {value}")
                return True
            else:
                error = result.get('error', 'unknown') if isinstance(result, dict) else 'invalid_response'
                print(f"   ❌ Element UI 填充失败: {placeholder} - {error}")
                return False
                
        except Exception as e:
            print(f"   ❌ Element UI 填充异常: {e}")
            return False
    
    @staticmethod
    def fill_by_label(
        tab_or_frame,
        label_text: str,
        value: Union[str, int, float]
    ) -> bool:
        """
        通过 Element UI 标签文本定位并填充
        
        查找 .el-form-item__label 中包含指定文本的标签，
        然后定位到对应的输入框进行填充。
        
        Args:
            tab_or_frame: DrissionPage 的 tab 或 frame 对象
            label_text: 标签文本（如 "用户名"、"身份证号"）
            value: 要填充的值
            
        Returns:
            填充是否成功
        """
        from ...utils.js_store import get_element_ui_label_fill_js
        
        try:
            js_code = get_element_ui_label_fill_js(label_text, str(value))
            result = tab_or_frame.run_js(js_code)
            
            if isinstance(result, dict) and result.get('success'):
                print(f"   ✅ 标签填充成功: [{label_text}] = {value}")
                return True
            else:
                error = result.get('error', 'unknown') if isinstance(result, dict) else 'invalid_response'
                print(f"   ❌ 标签填充失败: [{label_text}] - {error}")
                return False
                
        except Exception as e:
            print(f"   ❌ 标签填充异常: {e}")
            return False
    
    @classmethod
    def fill_in_iframe(
        cls,
        tab,
        placeholder: str,
        value: Union[str, int, float],
        iframe_index: int = 0
    ) -> bool:
        """
        自动切换到 Iframe 后填充
        
        Args:
            tab: DrissionPage 的 tab 对象
            placeholder: 输入框 placeholder
            value: 要填充的值
            iframe_index: Iframe 索引（默认第一个）
            
        Returns:
            填充是否成功
        """
        try:
            # 获取 Iframe
            iframes = tab.eles('tag:iframe')
            if not iframes or len(iframes) <= iframe_index:
                print(f"   ⚠️ 未找到 Iframe[{iframe_index}]")
                return False
            
            frame = tab.get_frame(iframes[iframe_index])
            if not frame:
                print(f"   ⚠️ 无法获取 Iframe 对象")
                return False
            
            return cls.fill_by_placeholder(frame, placeholder, value)
            
        except Exception as e:
            print(f"   ❌ Iframe 填充异常: {e}")
            return False
