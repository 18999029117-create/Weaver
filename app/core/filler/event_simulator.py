"""
事件模拟器模块

模拟完整的用户交互行为，触发 Vue/React 等框架的事件处理。

事件链:
1. Focus 阶段: focusin -> focus
2. 输入阶段: 清空 -> 设置值
3. Input 事件: input (InputEvent)
4. Change 事件: change
5. Blur 阶段: focusout -> blur
"""

from typing import Optional, Dict, Any, Union


class EventSimulator:
    """
    表单事件模拟器
    
    通过 JavaScript 模拟完整的用户交互行为，
    确保 Vue/React/Angular 等框架的事件处理正确触发。
    """
    
    @staticmethod
    def fill_with_events(
        tab_or_frame,
        elem_id: str = '',
        xpath: str = '',
        css_selector: str = '',
        value: Union[str, int, float] = '',
        elem_type: str = 'text',
        tag_name: str = 'input'
    ) -> bool:
        """
        使用完整事件链填充元素
        
        按顺序触发: Focus -> Clear -> Set Value -> Input -> Change -> Blur
        
        Args:
            tab_or_frame: DrissionPage 的 tab 或 frame 对象
            elem_id: 元素 ID
            xpath: XPath 选择器
            css_selector: CSS 选择器
            value: 要填充的值
            elem_type: 元素类型 (text, checkbox, radio, select 等)
            tag_name: 标签名
            
        Returns:
            填充是否成功
        """
        from ...utils.js_store import get_fill_with_events_js
        
        try:
            js_code = get_fill_with_events_js(
                elem_id=elem_id,
                xpath=xpath,
                css_selector=css_selector,
                value=str(value),
                elem_type=elem_type,
                tag_name=tag_name
            )
            
            result = tab_or_frame.run_js(js_code)
            
            if isinstance(result, dict) and result.get('success'):
                final_value = result.get('finalValue', '')
                return True
            else:
                error = result.get('error', 'unknown') if isinstance(result, dict) else 'invalid_response'
                print(f"   ⚠️ 事件填充失败: {error}")
                return False
                
        except Exception as e:
            print(f"   ❌ 事件模拟异常: {e}")
            return False
    
    @staticmethod
    def trigger_vue_events(
        tab_or_frame,
        xpath: str,
        value: str
    ) -> bool:
        """
        触发 Vue 双向绑定事件
        
        专门针对 Vue v-model 的事件触发：
        - input 事件（v-model 核心）
        - change 事件（表单验证）
        - blur 事件（失焦验证）
        
        Args:
            tab_or_frame: DrissionPage 的 tab 或 frame 对象
            xpath: 元素的 XPath
            value: 要设置的值
            
        Returns:
            是否成功
        """
        value_escaped = value.replace('\\', '\\\\').replace("'", "\\'")
        xpath_escaped = xpath.replace("'", "\\'").replace('"', '\\"')
        
        js_code = f"""
        (function() {{
            try {{
                let result = document.evaluate("{xpath_escaped}", document, null, 
                    XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                let el = result.singleNodeValue;
                
                if (!el) return {{ success: false, error: 'element_not_found' }};
                
                el.focus();
                el.value = '{value_escaped}';
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                el.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                el.blur();
                
                return {{ success: true, value: el.value }};
            }} catch (e) {{
                return {{ success: false, error: e.toString() }};
            }}
        }})();
        """
        
        try:
            result = tab_or_frame.run_js(js_code)
            return isinstance(result, dict) and result.get('success', False)
        except:
            return False
