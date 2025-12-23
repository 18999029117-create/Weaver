"""
JavaScript 脚本存储模块

将所有嵌入在 Python 中的 JavaScript 代码集中管理。
方便维护、测试和复用。

模块结构:
- PAGE_SCANNER_JS: 页面元素扫描脚本
- LOADING_DETECTOR_JS: 加载状态检测脚本
- ELEMENT_UI_FILLER_JS: Element UI 填充脚本
- EVENT_SIMULATOR_JS: Vue/React 事件模拟脚本
"""

from typing import Final


# ============================================================
# 加载状态检测器
# ============================================================
LOADING_DETECTOR_JS: Final[str] = """
(function() {
    const loaderSelectors = [
        '.ant-spin-spinning',           // Ant Design 旋转
        '.ant-spin-container.ant-spin-blur', // Ant Design 模糊遮罩
        '.el-loading-mask',             // ElementUI 加载遮罩
        '.el-loading-spinner',          // ElementUI 旋转
        '.v-loading',                   // Vue Loading
        '.ivu-spin',                    // iView/View UI
        '.van-loading',                 // Vant
        '.weui-loading',                // WeUI
        '.layui-layer-loading',         // LayUI
        '.modal-loading',               // 通用
        '[class*="loading"]:not(input):not(button)',
        '[class*="spinner"]:not(input)',
        '.skeleton', '.placeholder'
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
IFRAME_DETECTOR_JS: Final[str] = """
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
# Element UI 输入填充 (Vue 双向绑定兼容)
# ============================================================
def get_element_ui_fill_js(placeholder: str, value: str) -> str:
    """
    生成 Element UI 输入框填充 JS 代码
    
    Args:
        placeholder: 输入框 placeholder 文本
        value: 要填充的值
        
    Returns:
        可执行的 JavaScript 代码字符串
    """
    placeholder_escaped = placeholder.replace("'", "\\'").replace('"', '\\"')
    value_escaped = str(value).replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n')
    
    return f"""
    (function() {{
        let el = null;
        
        // 方法1: XPath by placeholder
        try {{
            const result = document.evaluate(
                "//input[@placeholder='{placeholder_escaped}']",
                document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
            );
            el = result.singleNodeValue;
        }} catch(e) {{}}
        
        // 方法2: CSS 选择器 (Element UI 专用)
        if (!el) {{
            el = document.querySelector('input.el-input__inner[placeholder="{placeholder_escaped}"]');
        }}
        
        // 方法3: 模糊匹配 placeholder
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
        
        // 设置值（Vue 双向绑定兼容）
        try {{
            el.focus();
            el.value = '';
            el.value = '{value_escaped}';
            
            // 触发 Vue 事件链
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
# Element UI 标签填充
# ============================================================
def get_element_ui_label_fill_js(label: str, value: str) -> str:
    """
    通过 Element UI 标签文本填充
    
    Args:
        label: 标签文本（如 "身份证号"）
        value: 要填充的值
    """
    label_escaped = label.replace("'", "\\'")
    value_escaped = str(value).replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"')
    
    return f"""
    (function() {{
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
            return {{ success: false, error: 'label_not_found', label: '{label_escaped}' }};
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


# ============================================================
# 通用事件模拟填充
# ============================================================
def get_fill_with_events_js(elem_id: str, xpath: str, css_selector: str, 
                             value: str, elem_type: str, tag_name: str) -> str:
    """
    生成通用的 JS 填充脚本，模拟完整用户行为
    
    行为链: Focus -> Clear -> Set Value -> Input Event -> Change Event -> Blur
    """
    value_escaped = value.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')
    elem_id_escaped = elem_id.replace("'", "\\'") if elem_id else ''
    xpath_escaped = xpath.replace("'", "\\'").replace('"', '\\"') if xpath else ''
    css_escaped = css_selector.replace("'", "\\'") if css_selector else ''
    
    return f"""
    (function() {{
        let el = null;
        
        // 多选择器定位元素
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
            // 1. Focus 阶段
            el.focus();
            el.dispatchEvent(new FocusEvent('focusin', {{ bubbles: true, cancelable: true }}));
            el.dispatchEvent(new FocusEvent('focus', {{ bubbles: false, cancelable: true }}));
            
            // 2. 清空并设置值
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
            
            // 3. 触发 Input 事件
            el.dispatchEvent(new Event('input', {{ bubbles: true, cancelable: true }}));
            el.dispatchEvent(new InputEvent('input', {{ 
                bubbles: true, 
                cancelable: true,
                data: '{value_escaped}',
                inputType: 'insertText'
            }}));
            
            // 4. 触发 Change 事件
            el.dispatchEvent(new Event('change', {{ bubbles: true, cancelable: true }}));
            
            // 5. Blur 阶段
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


# ============================================================
# 页面扫描主脚本（大型，保持原有功能）
# ============================================================
PAGE_SCANNER_JS: Final[str] = '''
function scanPage() {
    try {
        // 静默环境设置
        if (!window.__weaverSilentMode) {
            window.__weaverSilentMode = true;
            window.__originalAlert = window.alert;
            window.__originalConfirm = window.confirm;
            window.__originalPrompt = window.prompt;
            window.alert = (msg) => { console.log('[Weaver] Alert blocked:', msg); };
            window.confirm = (msg) => { console.log('[Weaver] Confirm auto-approved:', msg); return true; };
            window.prompt = (msg, def) => { console.log('[Weaver] Prompt auto-filled:', msg); return def || ''; };
        }
        
        // 加载状态探测
        function detectLoading() {
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
        }
        
        const loadStatus = detectLoading();
        if (loadStatus.status === 'loading') {
            return { status: 'loading', loader: loadStatus.loader, elements: [] };
        }
        
        const results = [];
        
        const INPUT_SELECTORS = [
            'input:not([type="hidden"]):not([type="button"]):not([type="submit"]):not([type="reset"]):not([type="image"]):not([type="file"])',
            'select', 'textarea', '[contenteditable="true"]',
            '[role="textbox"]', '[role="combobox"]', '[role="spinbutton"]'
        ].join(',');
        
        // 语义化 XPath 生成（禁止使用 ID）
        function getXPath(element) {
            if (!element) return '';
            if (element === document.body) return '/html/body';
            
            const ariaLabel = element.getAttribute('aria-label');
            if (ariaLabel) {
                return `//${element.tagName.toLowerCase()}[@aria-label="${ariaLabel}"]`;
            }
            
            const placeholder = element.placeholder;
            if (placeholder) {
                return `//${element.tagName.toLowerCase()}[@placeholder="${placeholder}"]`;
            }
            
            // 回退到位置 XPath
            let ix = 0;
            const siblings = element.parentNode ? element.parentNode.childNodes : [];
            for (let i = 0; i < siblings.length; i++) {
                const sibling = siblings[i];
                if (sibling === element) {
                    const parentPath = getXPath(element.parentNode);
                    return parentPath + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                }
                if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                    ix++;
                }
            }
            return '';
        }
        
        function getCSSSelector(element) {
            if (!element) return '';
            if (element.id) return '#' + CSS.escape(element.id);
            
            const parts = [];
            while (element && element.nodeType === Node.ELEMENT_NODE) {
                let selector = element.tagName.toLowerCase();
                if (element.className && typeof element.className === 'string') {
                    const classes = element.className.trim().split(/\\s+/).filter(c => c && !c.match(/^(ng-|v-|_)/));
                    if (classes.length > 0) {
                        selector += '.' + classes.slice(0, 2).map(c => CSS.escape(c)).join('.');
                    }
                }
                parts.unshift(selector);
                if (element.id || parts.length > 5) break;
                element = element.parentNode;
            }
            return parts.join(' > ');
        }
        
        function getLabelText(element) {
            const id = element.id;
            if (id) {
                const label = document.querySelector('label[for="' + CSS.escape(id) + '"]');
                if (label) return label.textContent.trim();
            }
            
            const parentLabel = element.closest('label');
            if (parentLabel) {
                const clone = parentLabel.cloneNode(true);
                clone.querySelectorAll('input, select, textarea').forEach(i => i.remove());
                return clone.textContent.trim();
            }
            
            const ariaLabel = element.getAttribute('aria-label');
            if (ariaLabel) return ariaLabel;
            
            // Element UI label
            const elFormItem = element.closest('.el-form-item');
            if (elFormItem) {
                const elLabel = elFormItem.querySelector('.el-form-item__label');
                if (elLabel) return elLabel.textContent.trim().replace(/[：:*]$/g, '');
            }
            
            return element.placeholder || element.name || element.id || '';
        }
        
        function getTableInfo(element) {
            const info = { is_table_cell: false, row_index: null, col_index: null, table_id: null, header_text: '' };
            let cell = element.closest('td, th');
            if (!cell) return info;
            
            info.is_table_cell = true;
            const row = cell.closest('tr');
            if (row) {
                info.row_index = row.rowIndex;
                info.col_index = cell.cellIndex;
            }
            
            const table = cell.closest('table');
            if (table) {
                info.table_id = table.id || table.className || 'table_' + Array.from(document.querySelectorAll('table')).indexOf(table);
            }
            
            return info;
        }
        
        function scanElements(root, shadowDepth = 0) {
            const elements = root.querySelectorAll(INPUT_SELECTORS);
            
            elements.forEach((el, idx) => {
                try {
                    const style = window.getComputedStyle(el);
                    if (style.display === 'none' || style.visibility === 'hidden') return;
                    
                    const rect = el.getBoundingClientRect();
                    const tableInfo = getTableInfo(el);
                    
                    const data = {
                        index: results.length,
                        tagName: el.tagName.toLowerCase(),
                        type: el.type || el.tagName.toLowerCase(),
                        name: el.name || '',
                        id: el.id || '',
                        className: typeof el.className === 'string' ? el.className : '',
                        placeholder: el.placeholder || '',
                        value: el.value || '',
                        
                        xpath: getXPath(el),
                        css_selector: getCSSSelector(el),
                        
                        label_text: getLabelText(el),
                        aria_label: el.getAttribute('aria-label') || '',
                        
                        rect: { x: Math.round(rect.x), y: Math.round(rect.y), width: Math.round(rect.width), height: Math.round(rect.height) },
                        
                        is_table_cell: tableInfo.is_table_cell,
                        row_index: tableInfo.row_index,
                        col_index: tableInfo.col_index,
                        table_id: tableInfo.table_id,
                        
                        disabled: el.disabled || false,
                        readonly: el.readOnly || false,
                        required: el.required || false,
                        shadow_depth: shadowDepth
                    };
                    
                    results.push(data);
                } catch (e) {}
            });
            
            // Shadow DOM 穿透
            if (shadowDepth < 2) {
                root.querySelectorAll('*').forEach(el => {
                    if (el.shadowRoot) {
                        try { scanElements(el.shadowRoot, shadowDepth + 1); } catch (e) {}
                    }
                });
            }
        }
        
        scanElements(document);
        return results;
        
    } catch (e) {
        return { error: e.toString(), stack: e.stack };
    }
}
return scanPage();
'''
