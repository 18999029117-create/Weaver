/**
 * Weaver 表单分析器 - 高性能 JS 扫描脚本
 * 
 * 功能:
 * - 一次执行返回所有可交互元素的完整信息
 * - 加载状态探测（Ant Design/ElementUI 等）
 * - 多重选择器生成（XPath/CSS/ID）
 * - 视觉坐标匹配（左侧/上方标题）
 * - Shadow DOM 穿透
 * - 表格 row_index 识别
 * 
 * @version 2.0
 */

function scanPage() {
    try {
        // ===== 静默环境设置 (劫持弹窗防止阻塞) =====
        if (!window.__weaverSilentMode) {
            window.__weaverSilentMode = true;
            window.__originalAlert = window.alert;
            window.__originalConfirm = window.confirm;
            window.__originalPrompt = window.prompt;
            window.alert = (msg) => { console.log('[Weaver] Alert blocked:', msg); };
            window.confirm = (msg) => { console.log('[Weaver] Confirm auto-approved:', msg); return true; };
            window.prompt = (msg, def) => { console.log('[Weaver] Prompt auto-filled:', msg); return def || ''; };
        }
        
        // ===== 加载状态探测 =====
        function detectLoading() {
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
                '[class*="loading"]:not(input):not(button)', // 模糊匹配
                '[class*="spinner"]:not(input)',
                '.skeleton', '.placeholder'     // 骨架屏
            ];
            
            for (let sel of loaderSelectors) {
                try {
                    let loader = document.querySelector(sel);
                    if (loader && loader.offsetParent !== null) {
                        // 检查是否可见
                        const style = window.getComputedStyle(loader);
                        if (style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0') {
                            return { status: 'loading', loader: sel };
                        }
                    }
                } catch(e) {}
            }
            
            // 检查 document.readyState
            if (document.readyState !== 'complete') {
                return { status: 'loading', loader: 'document.readyState=' + document.readyState };
            }
            
            return { status: 'ready' };
        }
        
        // 执行加载检测
        const loadStatus = detectLoading();
        if (loadStatus.status === 'loading') {
            return { status: 'loading', loader: loadStatus.loader, elements: [] };
        }
        
        const results = [];
        
        // ===== 配置 =====
        const INPUT_SELECTORS = [
            'input:not([type="hidden"]):not([type="button"]):not([type="submit"]):not([type="reset"]):not([type="image"]):not([type="file"])',
            'select',
            'textarea',
            '[contenteditable="true"]',
            '[role="textbox"]',
            '[role="combobox"]',
            '[role="spinbutton"]'
        ].join(',');
        
        // Autocomplete 下拉选项选择器
        const AUTOCOMPLETE_SELECTORS = [
            '.dropdown.show .dropdown-item',           // 通用下拉框
            '.dropdown-menu.show .dropdown-item',      // Bootstrap 风格
            '.autocomplete-dropdown .autocomplete-item',
            '[role="listbox"] [role="option"]',        // ARIA 标准
            '.el-autocomplete-suggestion li',          // ElementUI
            '.ant-select-dropdown .ant-select-item',   // Ant Design
            '.ant-cascader-menu-item',                 // Ant Design 级联
            '.el-select-dropdown__item',               // ElementUI Select
            '.ivu-select-dropdown .ivu-select-item',   // iView
            '.van-picker-column__item',                // Vant
            '.layui-table-tips-main li',               // LayUI
            'ul.ui-autocomplete li',                   // jQuery UI
            'datalist option'                          // HTML5 datalist
        ].join(',');
        
        // ===== 辅助函数 =====
        
        // ===== 政府级 Vue.js 站点专用: 语义化 XPath 生成 =====
        // 禁止使用 ID 选择器（因为 ID 包含随机哈希如 data-v-xxxx）
        // 改用基于标签文本的相对定位
        function getXPath(element) {
            if (!element) return '';
            if (element === document.body) {
                return '/html/body';
            }
            
            // ===== 策略1: 基于 aria-label 的 XPath（最稳定） =====
            const ariaLabel = element.getAttribute('aria-label');
            if (ariaLabel) {
                const tag = element.tagName.toLowerCase();
                return `//${tag}[@aria-label="${ariaLabel}"]`;
            }
            
            // ===== 策略2: 基于 placeholder 的 XPath =====
            const placeholder = element.placeholder;
            if (placeholder) {
                const tag = element.tagName.toLowerCase();
                return `//${tag}[@placeholder="${placeholder}"]`;
            }
            
            // ===== 策略3: 基于关联 Label 文本的相对 XPath =====
            // 查找 "包含文本 X 的 label 的兄弟/后代 input"
            const labelText = getLabelTextForXPath(element);
            if (labelText) {
                const tag = element.tagName.toLowerCase();
                // 生成：//label[contains(text(),'姓名')]/following-sibling::div//input
                // 或：//*[contains(text(),'姓名')]/ancestor::*[contains(@class,'form-item')]//input
                return `//*[contains(text(),"${labelText}")]/ancestor::*[contains(@class,"form-item") or contains(@class,"el-form-item")]//descendant::${tag}`;
            }
            
            // ===== 策略4: 基于表格列头的 XPath（表格场景） =====
            const tableCell = element.closest('td');
            if (tableCell) {
                const row = tableCell.closest('tr');
                const table = tableCell.closest('table');
                if (row && table) {
                    const colIndex = Array.from(row.cells).indexOf(tableCell) + 1;
                    const rowIndex = row.rowIndex + 1;
                    const tag = element.tagName.toLowerCase();
                    // 生成类似：//table//tr[3]/td[2]//input
                    return `//table//tr[${rowIndex}]/td[${colIndex}]//${tag}`;
                }
            }
            
            // ===== 策略5: Element UI 表格专用 =====
            const elTableRow = element.closest('.el-table__row');
            if (elTableRow) {
                const rows = Array.from(document.querySelectorAll('.el-table__row'));
                const rowIndex = rows.indexOf(elTableRow) + 1;
                const cells = elTableRow.querySelectorAll('.el-table__cell, td');
                let colIndex = 0;
                for (let cell of cells) {
                    colIndex++;
                    if (cell.contains(element)) break;
                }
                const tag = element.tagName.toLowerCase();
                return `//*[contains(@class,"el-table__row")][${rowIndex}]//*[contains(@class,"el-table__cell")][${colIndex}]//${tag}`;
            }
            
            // ===== 策略6: 回退 - 纯位置 XPath（不使用 ID）=====
            let ix = 0;
            const siblings = element.parentNode ? element.parentNode.childNodes : [];
            for (let i = 0; i < siblings.length; i++) {
                const sibling = siblings[i];
                if (sibling === element) {
                    const parentPath = getXPath(element.parentNode);
                    const tagName = element.tagName.toLowerCase();
                    return parentPath + '/' + tagName + '[' + (ix + 1) + ']';
                }
                if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                    ix++;
                }
            }
            return '';
        }
        
        // 辅助函数：获取用于 XPath 的 Label 文本
        function getLabelTextForXPath(element) {
            // 检查 Element UI form-item
            const elFormItem = element.closest('.el-form-item');
            if (elFormItem) {
                const label = elFormItem.querySelector('.el-form-item__label');
                if (label) {
                    const text = label.textContent.trim().replace(/[：:*]/g, '');
                    if (text.length > 0 && text.length < 20) return text;
                }
            }
            
            // 检查标准 label[for]
            if (element.id) {
                const labelFor = document.querySelector(`label[for="${element.id}"]`);
                if (labelFor) {
                    const text = labelFor.textContent.trim().replace(/[：:*]/g, '');
                    if (text.length > 0 && text.length < 20) return text;
                }
            }
            
            return '';
        }
        
        // 生成 CSS 选择器
        function getCSSSelector(element) {
            if (!element) return '';
            if (element.id) {
                return '#' + CSS.escape(element.id);
            }
            
            const parts = [];
            while (element && element.nodeType === Node.ELEMENT_NODE) {
                let selector = element.tagName.toLowerCase();
                if (element.className && typeof element.className === 'string') {
                    const classes = element.className.trim().split(/\s+/).filter(c => c && !c.match(/^(ng-|v-|_)/));
                    if (classes.length > 0) {
                        selector += '.' + classes.slice(0, 2).map(c => CSS.escape(c)).join('.');
                    }
                }
                
                // 添加 nth-child 确保唯一性
                const parent = element.parentNode;
                if (parent) {
                    const siblings = Array.from(parent.children).filter(e => e.tagName === element.tagName);
                    if (siblings.length > 1) {
                        const index = siblings.indexOf(element) + 1;
                        selector += ':nth-of-type(' + index + ')';
                    }
                }
                
                parts.unshift(selector);
                if (element.id || parts.length > 5) break;
                element = element.parentNode;
            }
            return parts.join(' > ');
        }
        
        // 获取视觉坐标附近的文本（左侧 / 上方 / 右侧，优先同容器）
        function getVisualLabel(element, rect) {
            if (!rect || rect.width === 0) return '';
            
            const searchRadiusX = 250;  // 左侧搜索半径
            const searchRadiusY = 60;   // 上方搜索半径
            const searchRadiusR = 200;  // 右侧搜索半径
            const maxVerticalGap = 150; // 最大垂直距离（避免跨section）
            let bestLabel = '';
            
            // 获取元素所在的容器（section/div/form）
            const elemContainer = element.closest('section, .space-y-6, form, [class*="card"], [class*="panel"]');
            
            // 收集候选文本节点
            const walker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_TEXT,
                {
                    acceptNode: function(node) {
                        const text = node.textContent.trim();
                        // 过滤空文本和过长文本
                        if (!text || text.length > 50 || text.length < 1) {
                            return NodeFilter.FILTER_REJECT;
                        }
                        return NodeFilter.FILTER_ACCEPT;
                    }
                }
            );
            
            let textNode;
            const candidates = [];
            
            while (textNode = walker.nextNode()) {
                const range = document.createRange();
                range.selectNodeContents(textNode);
                const textRect = range.getBoundingClientRect();
                
                if (textRect.width === 0 || textRect.height === 0) continue;
                
                // 检查垂直距离是否超限（防止跨section匹配）
                const verticalGap = Math.abs(textRect.top - rect.top);
                if (verticalGap > maxVerticalGap) continue;
                
                // 计算文本中心点
                const textCenterX = textRect.left + textRect.width / 2;
                const textCenterY = textRect.top + textRect.height / 2;
                
                // 元素左侧中心点
                const elemCenterY = rect.top + rect.height / 2;
                
                // 检查是否在同一容器内
                const textContainer = textNode.parentElement?.closest('section, .space-y-6, form, [class*="card"], [class*="panel"]');
                const sameContainer = (elemContainer && textContainer && elemContainer === textContainer);
                
                // 优先级1: 左侧文本 (在元素左边，且垂直位置接近)
                if (textCenterX < rect.left && Math.abs(textCenterY - elemCenterY) < 30) {
                    const distance = rect.left - textRect.right;
                    if (distance > 0 && distance < searchRadiusX) {
                        candidates.push({
                            text: textNode.textContent.trim(),
                            distance: distance,
                            priority: sameContainer ? 0.5 : 1, // 同容器优先
                            sameContainer: sameContainer
                        });
                    }
                }
                
                // 优先级2: 上方文本 (在元素上方，且水平位置接近)
                if (textCenterY < rect.top && Math.abs(textCenterX - rect.left) < rect.width + 50) {
                    const distance = rect.top - textRect.bottom;
                    if (distance > 0 && distance < searchRadiusY) {
                        candidates.push({
                            text: textNode.textContent.trim(),
                            distance: distance,
                            priority: sameContainer ? 1.5 : 2, // 同容器优先
                            sameContainer: sameContainer
                        });
                    }
                }
                
                // 优先级3: 右侧文本 (在元素右边，且垂直位置接近)
                if (textCenterX > rect.right && Math.abs(textCenterY - elemCenterY) < 30) {
                    const distance = textRect.left - rect.right;
                    if (distance > 0 && distance < searchRadiusR) {
                        candidates.push({
                            text: textNode.textContent.trim(),
                            distance: distance,
                            priority: sameContainer ? 2.5 : 3, // 同容器优先
                            sameContainer: sameContainer
                        });
                    }
                }
            }
            
            // 按优先级和距离排序（同容器内的优先）
            candidates.sort((a, b) => {
                // 先按同容器排序
                if (a.sameContainer !== b.sameContainer) {
                    return a.sameContainer ? -1 : 1;
                }
                // 再按优先级
                if (a.priority !== b.priority) return a.priority - b.priority;
                // 最后按距离
                return a.distance - b.distance;
            });
            
            if (candidates.length > 0) {
                bestLabel = candidates[0].text;
            }
            
            return bestLabel;
        }
        
        // 获取表格信息
        function getTableInfo(element) {
            const info = {
                is_table_cell: false,
                row_index: null,
                col_index: null,
                table_id: null,
                header_text: ''
            };
            
            // 向上查找 TD/TH
            let cell = element.closest('td, th');
            if (!cell) return info;
            
            info.is_table_cell = true;
            
            // 获取行
            const row = cell.closest('tr');
            if (row) {
                info.row_index = row.rowIndex;
                info.col_index = cell.cellIndex;
            }
            
            // 获取表格标识
            const table = cell.closest('table');
            if (table) {
                info.table_id = table.id || table.className || ('table_' + Array.from(document.querySelectorAll('table')).indexOf(table));
                
                // 尝试获取表头文字
                if (info.col_index !== null) {
                    // 先找 thead
                    const thead = table.querySelector('thead');
                    if (thead) {
                        const headerRow = thead.querySelector('tr');
                        if (headerRow) {
                            const th = headerRow.cells[info.col_index];
                            if (th) info.header_text = th.textContent.trim();
                        }
                    }
                    
                    // 没有 thead，找第一行
                    if (!info.header_text) {
                        const firstRow = table.querySelector('tr');
                        if (firstRow && firstRow !== row) {
                            const firstCell = firstRow.cells[info.col_index];
                            if (firstCell) {
                                info.header_text = firstCell.textContent.trim();
                            }
                        }
                    }
                }
            }
            
            return info;
        }
        
        // 获取关联的 Label 文本
        function getLabelText(element) {
            // 方法1: 通过 for 属性
            const id = element.id;
            if (id) {
                const label = document.querySelector('label[for="' + CSS.escape(id) + '"]');
                if (label) return label.textContent.trim();
            }
            
            // 方法2: 包裹在 label 内
            const parentLabel = element.closest('label');
            if (parentLabel) {
                // 获取 label 文本但排除 input 本身的文本
                const clone = parentLabel.cloneNode(true);
                const inputs = clone.querySelectorAll('input, select, textarea');
                inputs.forEach(i => i.remove());
                return clone.textContent.trim();
            }
            
            // 方法3: aria-label
            const ariaLabel = element.getAttribute('aria-label');
            if (ariaLabel) return ariaLabel;
            
            // 方法4: aria-labelledby
            const labelledBy = element.getAttribute('aria-labelledby');
            if (labelledBy) {
                const labelElem = document.getElementById(labelledBy);
                if (labelElem) return labelElem.textContent.trim();
            }
            
            // 方法5: 前一个相邻兄弟是 label（常见的表单布局模式）
            const prevSibling = element.previousElementSibling;
            if (prevSibling && prevSibling.tagName.toLowerCase() === 'label') {
                return prevSibling.textContent.trim();
            }
            
            // 方法6: 同一父 div 内的 label（常见的表单布局）
            const parent = element.parentElement;
            if (parent) {
                const siblingLabel = parent.querySelector('label');
                if (siblingLabel) {
                    // 确保这个 label 和当前元素在同一个直接父元素内
                    return siblingLabel.textContent.trim();
                }
            }
            
            return '';
        }
        
        // ===== Element UI / Ant Design 专用标签识别 =====
        function getElementUILabel(element) {
            // Element UI: el-form-item > .el-form-item__label
            const elFormItem = element.closest('.el-form-item');
            if (elFormItem) {
                const elLabel = elFormItem.querySelector('.el-form-item__label');
                if (elLabel) return elLabel.textContent.trim().replace(/[：:*]$/g, '');
            }
            
            // Ant Design: .ant-form-item > .ant-form-item-label
            const antFormItem = element.closest('.ant-form-item');
            if (antFormItem) {
                const antLabel = antFormItem.querySelector('.ant-form-item-label label, .ant-form-item-label');
                if (antLabel) return antLabel.textContent.trim().replace(/[：:*]$/g, '');
            }
            
            // iView/View UI
            const ivuFormItem = element.closest('.ivu-form-item');
            if (ivuFormItem) {
                const ivuLabel = ivuFormItem.querySelector('.ivu-form-item-label');
                if (ivuLabel) return ivuLabel.textContent.trim().replace(/[：:*]$/g, '');
            }
            
            return '';
        }
        
        // ===== 弹窗/对话框上下文检测 =====
        function getDialogContext(element) {
            // Element UI Dialog
            const elDialog = element.closest('.el-dialog');
            if (elDialog) {
                const title = elDialog.querySelector('.el-dialog__title');
                return title ? title.textContent.trim() : 'el-dialog';
            }
            
            // Ant Design Modal
            const antModal = element.closest('.ant-modal');
            if (antModal) {
                const title = antModal.querySelector('.ant-modal-title');
                return title ? title.textContent.trim() : 'ant-modal';
            }
            
            // Bootstrap/通用 Modal
            const modal = element.closest('.modal');
            if (modal) {
                const title = modal.querySelector('.modal-title');
                return title ? title.textContent.trim() : 'modal';
            }
            
            return '';
        }
        
        // ===== 主扫描逻辑 =====
        function scanElements(root, shadowDepth = 0) {
            const elements = root.querySelectorAll(INPUT_SELECTORS);
            
            elements.forEach((el, idx) => {
                try {
                    // 检查元素是否可见
                    const style = window.getComputedStyle(el);
                    if (style.display === 'none' || style.visibility === 'hidden') {
                        return;
                    }
                    
                    // 获取坐标
                    const rect = el.getBoundingClientRect();
                    
                    // 获取基础属性
                    const tagName = el.tagName.toLowerCase();
                    const inputType = el.type || tagName;
                    const name = el.name || '';
                    const id = el.id || '';
                    const className = el.className || '';
                    const placeholder = el.placeholder || '';
                    const value = el.value || '';
                    
                    // 获取 Label
                    let labelText = getLabelText(el);
                    
                    // 获取表格信息
                    const tableInfo = getTableInfo(el);
                    
                    // 如果表格有表头，优先使用
                    if (tableInfo.header_text && !labelText) {
                        labelText = tableInfo.header_text;
                    }
                    
                    // 如果仍然没有 label，使用视觉坐标匹配
                    let visualLabel = '';
                    if (!labelText) {
                        visualLabel = getVisualLabel(el, rect);
                        if (visualLabel) {
                            labelText = visualLabel;
                        }
                    }
                    
                    // 最终备选: placeholder -> name -> id
                    if (!labelText) {
                        labelText = placeholder || name || id || '';
                    }
                    
                    // 获取 Element UI / Ant Design 标签
                    const elFormLabel = getElementUILabel(el);
                    const ariaLabelDirect = el.getAttribute('aria-label') || '';
                    const dialogContext = getDialogContext(el);
                    
                    // 构造结果对象
                    const data = {
                        index: results.length,
                        tagName: tagName,
                        type: inputType,
                        name: name,
                        id: id,
                        className: typeof className === 'string' ? className : '',
                        placeholder: placeholder,
                        value: value,
                        
                        // 选择器
                        id_selector: id ? '#' + id : null,
                        xpath: getXPath(el),
                        css_selector: getCSSSelector(el),
                        
                        // 语义标签（原有）
                        label_text: labelText,
                        visual_label: visualLabel,
                        nearby_text: labelText,
                        
                        // 增强语义标签
                        aria_label: ariaLabelDirect,           // aria-label 直接值
                        el_form_label: elFormLabel,            // Element UI / Ant Design 表单标签
                        dialog_context: dialogContext,         // 弹窗上下文
                        
                        // 坐标
                        rect: {
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        },
                        
                        // 表格信息
                        is_table_cell: tableInfo.is_table_cell,
                        row_index: tableInfo.row_index,
                        col_index: tableInfo.col_index,
                        table_id: tableInfo.table_id,
                        table_header: tableInfo.header_text,
                        
                        // 状态
                        disabled: el.disabled || false,
                        readonly: el.readOnly || false,
                        required: el.required || false,
                        
                        // Shadow DOM 标记
                        shadow_depth: shadowDepth
                    };
                    
                    results.push(data);
                    
                } catch (e) {
                    // 单个元素失败不影响整体
                    console.warn('Element scan error:', e);
                }
            });
            
            // Shadow DOM 穿透 (至少2层深度)
            if (shadowDepth < 2) {
                const allElements = root.querySelectorAll('*');
                allElements.forEach(el => {
                    if (el.shadowRoot) {
                        try {
                            scanElements(el.shadowRoot, shadowDepth + 1);
                        } catch (e) {
                            console.warn('Shadow DOM scan error:', e);
                        }
                    }
                });
            }
        }
        
        // 执行扫描
        scanElements(document);
        
        // 扫描 Autocomplete 下拉选项
        function scanAutocompleteOptions() {
            const options = document.querySelectorAll(AUTOCOMPLETE_SELECTORS);
            options.forEach((el, idx) => {
                try {
                    const style = window.getComputedStyle(el);
                    if (style.display === 'none' || style.visibility === 'hidden') return;
                    
                    const rect = el.getBoundingClientRect();
                    if (rect.width === 0 || rect.height === 0) return;
                    
                    // 获取选项文本
                    const optionText = el.textContent.trim();
                    if (!optionText) return;
                    
                    // 查找关联的输入框
                    const wrapper = el.closest('.autocomplete-wrapper, [role="combobox"], .el-autocomplete, .ant-select');
                    let associatedInput = null;
                    if (wrapper) {
                        associatedInput = wrapper.querySelector('input');
                    }
                    
                    const data = {
                        index: results.length,
                        tagName: 'autocomplete-option',
                        type: 'option',
                        name: '',
                        id: el.id || '',
                        className: typeof el.className === 'string' ? el.className : '',
                        
                        // 选择器
                        xpath: getXPath(el),
                        css_selector: getCSSSelector(el),
                        
                        // 语义信息
                        label_text: optionText,
                        option_text: optionText,
                        nearby_text: optionText,
                        
                        // 坐标
                        rect: {
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        },
                        
                        // 标记为 Autocomplete 选项
                        is_autocomplete_option: true,
                        associated_input: associatedInput ? getXPath(associatedInput) : null
                    };
                    
                    results.push(data);
                } catch (e) {
                    console.warn('Autocomplete option scan error:', e);
                }
            });
        }
        
        scanAutocompleteOptions();
        
        return results;
        
    } catch (e) {
        return { error: e.toString(), stack: e.stack };
    }
}

// 导出入口
return scanPage();
