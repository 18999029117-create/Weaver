"""
JavaScript 脚本存储模块 - 基础设施层实现

将所有嵌入在 Python 中的 JavaScript 代码集中管理。
方便维护、测试和复用。

模块结构:
- PAGE_SCANNER_JS: 页面元素扫描脚本
- LOADING_DETECTOR_JS: 加载状态检测脚本
- ELEMENT_UI_FILLER_JS: Element UI 填充脚本
- EVENT_SIMULATOR_JS: Vue/React 事件模拟脚本
- FORM_ANALYZER_JS: 表单分析器脚本（外部文件）
"""

from typing import Final, Optional
from pathlib import Path

# 缓存外部 JS 文件内容
_form_analyzer_js_cache: Optional[str] = None


class ScriptStore:
    """
    JavaScript 脚本存储
    
    集中管理所有 JavaScript 脚本，提供类型安全的访问方式。
    """
    
    # ============================================================
    # 表单分析器脚本（从外部文件加载）
    # ============================================================
    @staticmethod
    def get_form_analyzer_js() -> str:
        """
        加载表单分析 JS 脚本
        
        从独立的 form_analyzer.js 文件加载脚本内容。
        使用缓存避免重复读取文件。
        
        Returns:
            JavaScript 代码字符串
        """
        global _form_analyzer_js_cache
        
        if _form_analyzer_js_cache is not None:
            return _form_analyzer_js_cache
        
        try:
            js_path = Path(__file__).parent / "form_analyzer.js"
            if js_path.exists():
                _form_analyzer_js_cache = js_path.read_text(encoding="utf-8")
                return _form_analyzer_js_cache
            else:
                print(f"[ScriptStore] form_analyzer.js not found at {js_path}")
                return ""
        except Exception as e:
            print(f"[ScriptStore] Failed to load form_analyzer.js: {e}")
            return ""
    
    # ============================================================
    # 加载状态检测器
    # ============================================================
    LOADING_DETECTOR: Final[str] = """
    (function() {
        const loaderSelectors = [
            '.ant-spin-spinning', '.ant-spin-container.ant-spin-blur',
            '.el-loading-mask', '.el-loading-spinner', '.v-loading',
            '.ivu-spin', '.van-loading', '.weui-loading', '.layui-layer-loading',
            '.modal-loading', '[class*="loading"]:not(input):not(button)',
            '[class*="spinner"]:not(input)', '.skeleton', '.placeholder'
        ];
        
        for (let sel of loaderSelectors) {
            try {
                let loader = document.querySelector(sel);
                if (loader && loader.offsetParent !== null) {
                    const style = window.getComputedStyle(loader);
                    if (style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0') {
                        return { status: 'loading', loader: sel };
                    }
                }
            } catch(e) {}
        }
        
        if (document.readyState !== 'complete') {
            return { status: 'loading', loader: 'document.readyState=' + document.readyState };
        }
        
        return { status: 'ready' };
    })();
    """
    
    # ============================================================
    # Iframe 检测器
    # ============================================================
    IFRAME_DETECTOR: Final[str] = """
    (function() {
        const iframes = document.querySelectorAll('iframe');
        return Array.from(iframes).map((iframe, i) => ({
            index: i,
            id: iframe.id || '',
            name: iframe.name || '',
            src: iframe.src || '',
            className: iframe.className || '',
            rect: {
                width: iframe.getBoundingClientRect().width,
                height: iframe.getBoundingClientRect().height
            }
        }));
    })();
    """
    
    # ============================================================
    # 翻页按钮检测器
    # ============================================================
    PAGINATION_DETECTOR: Final[str] = """
    (function() {
        const keywords = ['下一页', '下一条', 'Next', 'next', '下页', '后一页', 
                          '翻页', '下一步', '向后', '››', '»', '>>', '>', '→'];
        const results = [];
        
        const elements = document.querySelectorAll('button, a, [role="button"], input[type="button"], input[type="submit"], .btn, .page-btn');
        
        elements.forEach((el, idx) => {
            const text = (el.innerText || el.textContent || el.value || el.getAttribute('aria-label') || el.getAttribute('title') || '').trim();
            const className = el.className || '';
            const id = el.id || '';
            
            let isMatch = false;
            let matchKeyword = '';
            
            for (let kw of keywords) {
                if (text.includes(kw) || className.toLowerCase().includes('next') || id.toLowerCase().includes('next')) {
                    isMatch = true;
                    matchKeyword = text || kw;
                    break;
                }
            }
            
            if (isMatch && text.length < 50) {
                let xpath = '';
                if (el.id) {
                    xpath = `//*[@id="${el.id}"]`;
                } else {
                    let path = [];
                    let current = el;
                    while (current && current !== document.body) {
                        let tag = current.tagName.toLowerCase();
                        let parent = current.parentElement;
                        if (parent) {
                            let siblings = Array.from(parent.children).filter(c => c.tagName === current.tagName);
                            if (siblings.length > 1) {
                                let index = siblings.indexOf(current) + 1;
                                tag += '[' + index + ']';
                            }
                        }
                        path.unshift(tag);
                        current = parent;
                    }
                    xpath = '//' + path.join('/');
                }
                
                results.push({
                    text: matchKeyword.substring(0, 30),
                    tagName: el.tagName.toLowerCase(),
                    id: el.id || '',
                    className: (el.className || '').substring(0, 50),
                    xpath: xpath
                });
            }
        });
        
        return results;
    })();
    """
    
    # ============================================================
    # 元素高亮脚本模板
    # ============================================================
    @staticmethod
    def get_highlight_script(elem_id: str, css_selector: str, xpath: str, shadow_depth: int = 0, shadow_host_id: str = '') -> str:
        """
        生成元素高亮脚本
        
        Args:
            elem_id: 元素 ID
            css_selector: CSS 选择器
            xpath: XPath 选择器
            shadow_depth: Shadow DOM 深度
            shadow_host_id: Shadow Host ID
            
        Returns:
            JavaScript 代码
        """
        return f"""
        (function() {{
            let el = null;
            
            function findInShadowDOM(hostSelector, targetSelector) {{
                try {{
                    const hosts = document.querySelectorAll('*');
                    for (let host of hosts) {{
                        if (host.shadowRoot) {{
                            let found = host.shadowRoot.querySelector('input, textarea, select');
                            if (found) return found;
                        }}
                    }}
                }} catch(e) {{}}
                return null;
            }}
            
            if ({shadow_depth} > 0) {{
                el = findInShadowDOM('{shadow_host_id}', 'input, textarea, select');
            }}
            
            if (!el && '{elem_id}') {{
                el = document.getElementById('{elem_id}');
            }}
            
            if (!el && '{css_selector}') {{
                try {{ el = document.querySelector('{css_selector}'); }} catch(e) {{}}
            }}
            
            if (!el && `{xpath}`) {{
                try {{
                    let result = document.evaluate(`{xpath}`, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                    el = result.singleNodeValue;
                }} catch(e) {{}}
            }}
            
            if (el) {{
                el.scrollIntoView({{behavior: "smooth", block: "center"}});
                
                let originalBorder = el.style.border;
                let originalBg = el.style.backgroundColor;
                let originalOutline = el.style.outline;
                let originalBoxShadow = el.style.boxShadow;
                
                el.style.transition = 'all 0.15s ease-in-out';
                el.style.border = '1px solid #8E8E93';
                el.style.outline = '2px solid #636366';
                el.style.boxShadow = '0 0 0 4px rgba(99, 99, 102, 0.2)';
                el.style.backgroundColor = 'rgba(142, 142, 147, 0.12)';
                
                let count = 0;
                let flashInterval = setInterval(() => {{
                    if (count % 2 === 0) {{
                        el.style.backgroundColor = 'rgba(142, 142, 147, 0.15)';
                    }} else {{
                        el.style.backgroundColor = 'rgba(142, 142, 147, 0.08)';
                    }}
                    count++;
                    if (count >= 6) {{
                        clearInterval(flashInterval);
                        setTimeout(() => {{
                            el.style.border = originalBorder;
                            el.style.backgroundColor = originalBg;
                            el.style.outline = originalOutline;
                            el.style.boxShadow = originalBoxShadow;
                        }}, 300);
                    }}
                }}, 150);
                
                return true;
            }}
            return false;
        }})();
        """
    
    # ============================================================
    # Element UI 填充脚本
    # ============================================================
    @staticmethod
    def get_element_ui_fill(placeholder: str, value: str) -> str:
        """
        生成 Element UI 输入框填充脚本
        
        Args:
            placeholder: 输入框 placeholder
            value: 填充值
            
        Returns:
            JavaScript 代码
        """
        placeholder_escaped = placeholder.replace("'", "\\'").replace('"', '\\"')
        value_escaped = str(value).replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n')
        
        return f"""
        (function() {{
            let el = null;
            
            try {{
                const result = document.evaluate(
                    "//input[@placeholder='{placeholder_escaped}']",
                    document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
                );
                el = result.singleNodeValue;
            }} catch(e) {{}}
            
            if (!el) {{
                el = document.querySelector('input.el-input__inner[placeholder="{placeholder_escaped}"]');
            }}
            
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
                return {{ success: false, error: 'element_not_found', placeholder: '{placeholder_escaped}' }};
            }}
            
            try {{
                el.focus();
                el.value = '';
                el.value = '{value_escaped}';
                
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                el.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                el.blur();
                
                return {{ 
                    success: true, 
                    value: el.value,
                    placeholder: el.placeholder
                }};
                
            }} catch (e) {{
                return {{ success: false, error: e.toString() }};
            }}
        }})();
        """
    
    # ============================================================
    # 通用事件填充脚本
    # ============================================================
    @staticmethod
    def get_fill_with_events(elem_id: str, xpath: str, css_selector: str, 
                             value: str, elem_type: str = 'text', tag_name: str = 'input') -> str:
        """
        生成通用的填充脚本，模拟完整用户行为
        
        Args:
            elem_id: 元素 ID
            xpath: XPath 选择器
            css_selector: CSS 选择器
            value: 填充值
            elem_type: 元素类型
            tag_name: 标签名
            
        Returns:
            JavaScript 代码
        """
        value_escaped = value.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')
        elem_id_escaped = elem_id.replace("'", "\\'") if elem_id else ''
        xpath_escaped = xpath.replace("'", "\\'").replace('"', '\\"') if xpath else ''
        css_escaped = css_selector.replace("'", "\\'") if css_selector else ''
        
        return f"""
        (function() {{
            let el = null;
            
            if (!el && '{elem_id_escaped}') {{
                el = document.getElementById('{elem_id_escaped}');
            }}
            if (!el && '{css_escaped}') {{
                try {{ el = document.querySelector('{css_escaped}'); }} catch(e) {{}}
            }}
            if (!el && '{xpath_escaped}') {{
                try {{
                    let result = document.evaluate("{xpath_escaped}", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                    el = result.singleNodeValue;
                }} catch(e) {{}}
            }}
            
            if (!el) {{
                return {{ success: false, error: 'element_not_found' }};
            }}
            
            try {{
                el.focus();
                el.dispatchEvent(new FocusEvent('focusin', {{ bubbles: true, cancelable: true }}));
                el.dispatchEvent(new FocusEvent('focus', {{ bubbles: false, cancelable: true }}));
                
                let tagName = el.tagName.toLowerCase();
                let inputType = (el.type || 'text').toLowerCase();
                
                if (tagName === 'select') {{
                    let matched = false;
                    for (let opt of el.options) {{
                        if (opt.value === '{value_escaped}' || opt.text === '{value_escaped}') {{
                            el.value = opt.value;
                            matched = true;
                            break;
                        }}
                    }}
                }} else if (inputType === 'checkbox' || inputType === 'radio') {{
                    let shouldCheck = '{value_escaped}'.toLowerCase() === 'true' || 
                                     '{value_escaped}' === '1' || 
                                     '{value_escaped}' === '是';
                    if (el.checked !== shouldCheck) {{
                        el.checked = shouldCheck;
                    }}
                }} else {{
                    el.value = '';
                    el.value = '{value_escaped}';
                }}
                
                el.dispatchEvent(new Event('input', {{ bubbles: true, cancelable: true }}));
                el.dispatchEvent(new InputEvent('input', {{ 
                    bubbles: true, 
                    cancelable: true,
                    data: '{value_escaped}',
                    inputType: 'insertText'
                }}));
                
                el.dispatchEvent(new Event('change', {{ bubbles: true, cancelable: true }}));
                
                el.dispatchEvent(new FocusEvent('focusout', {{ bubbles: true, cancelable: true }}));
                el.dispatchEvent(new FocusEvent('blur', {{ bubbles: false, cancelable: true }}));
                el.blur();
                
                return {{ 
                    success: true, 
                    finalValue: el.value,
                    tagName: tagName,
                    inputType: inputType
                }};
                
            }} catch (e) {{
                return {{ success: false, error: e.toString(), stack: e.stack }};
            }}
        }})();
        """
