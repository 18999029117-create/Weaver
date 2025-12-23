"""
Element UI 表单适配器

专为 Vue.js + Element UI 框架优化的表单填充方法。
适用于政府级 SPA 应用（如医保、社保系统）。

功能:
- 自动 iframe 切换
- Vue 双向绑定兼容
- 支持 placeholder 和 label 两种定位方式
"""

from typing import Any, Optional


class ElementUIAdapter:
    """
    Element UI 表单适配器
    
    提供针对 Element UI 组件库的专用填充方法。
    支持 Vue.js 的双向绑定机制。
    """
    
    @staticmethod
    def fill_by_placeholder(
        tab: Any, 
        placeholder_text: str, 
        value: str, 
        ensure_iframe: bool = True
    ) -> bool:
        """
        通过 placeholder 文本定位并填充 Element UI 输入框
        
        Args:
            tab: DrissionPage 的 tab 对象
            placeholder_text: 输入框的 placeholder 文本
            value: 要填充的值
            ensure_iframe: 是否自动切换到 iframe
            
        Returns:
            bool: 是否成功
        """
        try:
            # 切换到 iframe
            if ensure_iframe:
                try:
                    js_check_iframe = """
                    (() => {
                        const iframes = document.querySelectorAll('iframe');
                        return iframes.length > 0;
                    })();
                    """
                    has_iframe = tab.run_js(js_check_iframe)
                    if has_iframe:
                        tab.to_frame(0)
                except Exception:
                    pass
            
            # 转义特殊字符
            placeholder_escaped = placeholder_text.replace("'", "\\'").replace('"', '\\"')
            value_escaped = str(value).replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n')
            
            js_fill = f"""
            (() => {{
                let el = null;
                
                // XPath by placeholder
                try {{
                    const result = document.evaluate(
                        "//input[@placeholder='{placeholder_escaped}']",
                        document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
                    );
                    el = result.singleNodeValue;
                }} catch(e) {{}}
                
                // CSS 选择器 (Element UI)
                if (!el) {{
                    el = document.querySelector('input.el-input__inner[placeholder="{placeholder_escaped}"]');
                }}
                
                // 模糊匹配
                if (!el) {{
                    const inputs = document.querySelectorAll('input.el-input__inner, input');
                    for (let inp of inputs) {{
                        if (inp.placeholder && inp.placeholder.includes('{placeholder_escaped}')) {{
                            el = inp;
                            break;
                        }}
                    }}
                }}
                
                if (!el) {{
                    return {{ success: false, error: 'element_not_found' }};
                }}
                
                // 设置值 (Vue 双向绑定兼容)
                el.focus();
                el.value = '';
                el.value = '{value_escaped}';
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                el.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                el.blur();
                
                return {{ success: true, value: el.value }};
            }})();
            """
            
            result = tab.run_js(js_fill)
            
            if result and isinstance(result, dict) and result.get('success'):
                print(f"   ✅ [{placeholder_text}] = {value}")
                return True
            else:
                print(f"   ❌ 填充失败: {result.get('error') if result else 'unknown'}")
                return False
                
        except Exception as e:
            print(f"   ❌ Element UI 填充异常: {e}")
            return False
            
        finally:
            if ensure_iframe:
                try:
                    tab.to_main()
                except:
                    pass
    
    @staticmethod
    def fill_by_label(
        tab: Any, 
        label_text: str, 
        value: str, 
        ensure_iframe: bool = True
    ) -> bool:
        """
        通过 Element UI 表单标签文本填充 (.el-form-item__label)
        
        Args:
            tab: DrissionPage 的 tab 对象
            label_text: 标签文本（如 "身份证号"、"姓名"）
            value: 要填充的值
            ensure_iframe: 是否自动切换到 iframe
            
        Returns:
            bool: 是否成功
        """
        try:
            if ensure_iframe:
                try:
                    tab.to_frame(0)
                except:
                    pass
            
            label_escaped = label_text.replace("'", "\\'")
            value_escaped = str(value).replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"')
            
            js_fill = f"""
            (() => {{
                const labels = document.querySelectorAll('.el-form-item__label');
                let targetInput = null;
                
                for (let label of labels) {{
                    const text = label.textContent.trim().replace(/[：:*]/g, '');
                    if (text === '{label_escaped}' || text.includes('{label_escaped}')) {{
                        const formItem = label.closest('.el-form-item');
                        if (formItem) {{
                            targetInput = formItem.querySelector('input.el-input__inner, textarea.el-textarea__inner, input');
                            if (targetInput) break;
                        }}
                    }}
                }}
                
                if (!targetInput) {{
                    return {{ success: false, error: 'label_not_found' }};
                }}
                
                targetInput.focus();
                targetInput.value = '';
                targetInput.value = '{value_escaped}';
                targetInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                targetInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                targetInput.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                targetInput.blur();
                
                return {{ success: true, value: targetInput.value }};
            }})();
            """
            
            result = tab.run_js(js_fill)
            
            if result and result.get('success'):
                print(f"   ✅ [标签:{label_text}] = {value}")
                return True
            else:
                print(f"   ❌ 标签 '{label_text}' 填充失败")
                return False
                
        except Exception as e:
            print(f"   ❌ Element UI 标签填充异常: {e}")
            return False
            
        finally:
            if ensure_iframe:
                try:
                    tab.to_main()
                except:
                    pass


# 向后兼容别名
fill_element_ui_input = ElementUIAdapter.fill_by_placeholder
fill_element_ui_by_label = ElementUIAdapter.fill_by_label
