/**
 * Weaver - Interactive Element Picking Script
 * 
 * 功能：
 * 1. 悬停高亮（灰色边框）
 * 2. 双击选择元素
 * 3. 闪烁动画反馈
 * 4. 智能识别表头/列关系
 */

(function () {
    'use strict';

    // 防止重复注入
    if (window.__weaver_interaction_injected) {
        console.log('[Weaver] Interaction script already injected.');
        return;
    }
    window.__weaver_interaction_injected = true;

    // ============================================================
    // 全局状态
    // ============================================================
    window.weaver_picked_element = null;  // 存储被选中的元素信息
    window.weaver_pick_mode = true;       // 选择模式开关

    // 样式常量（黑白风格）
    const HOVER_BORDER_COLOR = '#000000';  // 黑色边框，更醒目
    const HOVER_BORDER_WIDTH = '2px';
    const FLASH_BG_COLOR_1 = 'rgba(0, 0, 0, 0.2)';
    const FLASH_BG_COLOR_2 = 'rgba(0, 0, 0, 0.05)';

    // 注入样式
    const styleId = 'weaver-interaction-styles';
    if (!document.getElementById(styleId)) {
        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            .weaver-hover {
                outline: ${HOVER_BORDER_WIDTH} solid ${HOVER_BORDER_COLOR} !important;
                outline-offset: 1px !important;
                cursor: pointer !important;
            }
            .weaver-flash {
                animation: weaver-flash-anim 0.3s ease-in-out 3;
            }
            @keyframes weaver-flash-anim {
                0%, 100% { background-color: ${FLASH_BG_COLOR_2}; }
                50% { background-color: ${FLASH_BG_COLOR_1}; }
            }
        `;
        document.head.appendChild(style);
    }

    // ============================================================
    // 工具函数
    // ============================================================

    /**
     * 生成元素的简单 XPath
     */
    function getXPath(el) {
        if (!el || el.nodeType !== 1) return '';

        // 优先使用 ID
        if (el.id) {
            return `//*[@id="${el.id}"]`;
        }

        const parts = [];
        let current = el;

        while (current && current !== document.body && current !== document.documentElement) {
            let tag = current.tagName.toLowerCase();
            const parent = current.parentElement;

            if (parent) {
                const siblings = Array.from(parent.children).filter(c => c.tagName === current.tagName);
                if (siblings.length > 1) {
                    const index = siblings.indexOf(current) + 1;
                    tag += `[${index}]`;
                }
            }
            parts.unshift(tag);
            current = parent;
        }

        return '//' + parts.join('/');
    }

    /**
     * 获取元素的 CSS 选择器
     */
    function getCssSelector(el) {
        if (!el || el.nodeType !== 1) return '';

        if (el.id) {
            return `#${el.id}`;
        }

        const parts = [];
        let current = el;

        while (current && current !== document.body) {
            let selector = current.tagName.toLowerCase();

            if (current.className && typeof current.className === 'string') {
                const classes = current.className.trim().split(/\s+/).filter(c => c && !c.includes(':'));
                if (classes.length > 0) {
                    selector += '.' + classes.slice(0, 2).join('.');
                }
            }

            parts.unshift(selector);
            current = current.parentElement;
        }

        return parts.join(' > ');
    }

    /**
     * 判断元素是否是可输入元素（扩展检测）
     */
    function isInputElement(el) {
        if (!el) return false;
        const tag = el.tagName.toLowerCase();

        // 标准输入元素
        if (['input', 'textarea', 'select'].includes(tag)) return true;

        // contenteditable
        if (el.isContentEditable || el.getAttribute('contenteditable') === 'true') return true;

        // 常见 UI 框架的输入组件
        const className = (el.className || '').toLowerCase();
        const inputClasses = [
            'el-input', 'ant-input', 'ivu-input', 'arco-input',  // 主流框架
            'form-control', 'text-field', 'textbox',              // Bootstrap/通用
            'input-text', 'inputtext', 'edit-cell',               // 表格编辑
            'layui-input', 'weui-input'                           // 其他框架
        ];
        if (inputClasses.some(cls => className.includes(cls))) return true;

        // 有 role="textbox" 或 role="combobox" 的元素
        const role = el.getAttribute('role');
        if (role === 'textbox' || role === 'combobox' || role === 'listbox' || role === 'spinbutton') return true;

        // 检查父元素是否是输入包装器
        const parent = el.parentElement;
        if (parent) {
            const parentClass = (parent.className || '').toLowerCase();
            if (parentClass.includes('input') || parentClass.includes('edit')) {
                // 如果父元素是输入框，当前元素也算
                return true;
            }
        }

        return false;
    }

    /**
     * 判断元素是否可能是表头或标签
     */
    function isHeaderElement(el) {
        if (!el) return false;
        const tag = el.tagName.toLowerCase();

        // 常见表头标签
        if (['th', 'label', 'legend', 'dt'].includes(tag)) return true;

        // 表头类名
        const className = (el.className || '').toLowerCase();
        const headerClasses = [
            'header', 'label', 'title', 'col-name', 'column-title',
            'table-head', 'th-', 'field-label', 'form-label',
            'el-form-item__label', 'ant-form-item-label'  // 常见框架
        ];
        if (headerClasses.some(cls => className.includes(cls))) return true;

        // 父元素是 thead
        if (el.closest('thead')) return true;

        return false;
    }

    /**
     * 判断元素是否可交互（仅输入框，不含表头）
     */
    function isInteractiveElement(el) {
        if (!el) return false;
        // 只允许输入框元素被高亮和选择，不包括表头
        return isInputElement(el);
    }

    /**
     * 查找输入框的父级标题/标签文本
     */
    function findParentHeaderText(inputEl) {
        if (!inputEl) return '';

        // 方法1：查找关联的 label[for]
        if (inputEl.id) {
            const label = document.querySelector(`label[for="${inputEl.id}"]`);
            if (label) return label.textContent.trim();
        }

        // 方法2：查找父级 label
        const parentLabel = inputEl.closest('label');
        if (parentLabel) {
            return parentLabel.textContent.replace(inputEl.value || '', '').trim();
        }

        // 方法3：在表格中，查找同列的表头
        const td = inputEl.closest('td');
        if (td) {
            const tr = td.parentElement;
            const table = td.closest('table');
            if (tr && table) {
                const cellIndex = Array.from(tr.children).indexOf(td);
                const thead = table.querySelector('thead tr, tr:first-child');
                if (thead && thead.children[cellIndex]) {
                    return thead.children[cellIndex].textContent.trim();
                }
            }
        }

        // 方法4：查找前一个兄弟元素（常见于表单布局）
        const prev = inputEl.previousElementSibling;
        if (prev && (prev.tagName.toLowerCase() === 'label' || prev.tagName.toLowerCase() === 'span')) {
            return prev.textContent.trim();
        }

        // 方法5：查找 form-item 容器中的 label
        const formItem = inputEl.closest('.el-form-item, .ant-form-item, .form-group, .form-item');
        if (formItem) {
            const label = formItem.querySelector('label, .el-form-item__label, .ant-form-item-label');
            if (label) return label.textContent.trim().replace(':', '').replace('：', '');
        }

        return '';
    }

    /**
     * 查找同级输入框（同行或同列）
     */
    function findSiblingInputs(inputEl) {
        const siblings = [];

        // 方法1：表格中查找同列输入框
        const td = inputEl.closest('td');
        if (td) {
            const table = td.closest('table');
            const tr = td.parentElement;
            if (table && tr) {
                const cellIndex = Array.from(tr.children).indexOf(td);
                const rows = table.querySelectorAll('tbody tr, tr');
                rows.forEach(row => {
                    if (row.children[cellIndex]) {
                        const inputs = row.children[cellIndex].querySelectorAll('input, textarea, select');
                        inputs.forEach(inp => {
                            if (inp !== inputEl) siblings.push(inp);
                        });
                    }
                });
            }
        }

        // 方法2：表单分组中查找同类输入框
        if (siblings.length === 0) {
            const formContainer = inputEl.closest('form, .form-container, .el-form, .ant-form');
            if (formContainer) {
                // 找有相同 name 或相同 class 的输入框
                const inputName = inputEl.name;
                const inputClass = inputEl.className;
                if (inputName) {
                    const sameNameInputs = formContainer.querySelectorAll(`input[name="${inputName}"], textarea[name="${inputName}"]`);
                    sameNameInputs.forEach(inp => {
                        if (inp !== inputEl) siblings.push(inp);
                    });
                }
            }
        }

        return siblings;
    }


    /**
     * 查找与表头关联的所有输入元素（同列或同行）
     */
    function findRelatedInputs(headerEl) {
        const inputs = [];

        // 方法1：如果在表格中，查找同列
        const table = headerEl.closest('table');
        if (table) {
            const headerCell = headerEl.closest('th, td');
            if (headerCell) {
                const row = headerCell.parentElement;
                const cellIndex = Array.from(row.children).indexOf(headerCell);

                // 遍历表格所有行，获取同列的输入框
                const rows = table.querySelectorAll('tr');
                rows.forEach(tr => {
                    const cells = tr.children;
                    if (cells[cellIndex]) {
                        const cellInputs = cells[cellIndex].querySelectorAll('input, textarea, select');
                        cellInputs.forEach(inp => inputs.push(inp));
                    }
                });
            }
        }

        // 方法2：查找 for 属性关联
        if (headerEl.tagName.toLowerCase() === 'label' && headerEl.htmlFor) {
            const target = document.getElementById(headerEl.htmlFor);
            if (target) inputs.push(target);
        }

        // 方法3：查找同一父容器下的输入框（表单分组）
        const container = headerEl.closest('.form-group, .form-item, .el-form-item, .ant-form-item, .field');
        if (container) {
            const containerInputs = container.querySelectorAll('input, textarea, select');
            containerInputs.forEach(inp => {
                if (!inputs.includes(inp)) inputs.push(inp);
            });
        }

        return inputs;
    }

    /**
     * 收集元素指纹信息
     */
    function collectFingerprint(el) {
        const tag = el.tagName.toLowerCase();
        const rect = el.getBoundingClientRect();

        // 查找附近的标签文本
        let labelText = '';

        // 1. 检查 label[for]
        if (el.id) {
            const label = document.querySelector(`label[for="${el.id}"]`);
            if (label) labelText = label.textContent.trim();
        }

        // 2. 检查父级 label
        if (!labelText) {
            const parentLabel = el.closest('label');
            if (parentLabel) {
                labelText = parentLabel.textContent.replace(el.value || '', '').trim();
            }
        }

        // 3. 检查前一个兄弟元素
        if (!labelText && el.previousElementSibling) {
            const prev = el.previousElementSibling;
            if (prev.tagName.toLowerCase() === 'label' || prev.tagName.toLowerCase() === 'span') {
                labelText = prev.textContent.trim();
            }
        }

        // 4. 使用 placeholder 或 aria-label
        if (!labelText) {
            labelText = el.placeholder || el.getAttribute('aria-label') || el.getAttribute('title') || '';
        }

        return {
            xpath: getXPath(el),
            css_selector: getCssSelector(el),
            tag_name: tag,
            element_id: el.id || '',
            element_name: el.name || '',
            element_class: el.className || '',
            input_type: el.type || '',
            placeholder: el.placeholder || '',
            label_text: labelText.substring(0, 100),
            aria_label: el.getAttribute('aria-label') || '',
            rect: {
                x: Math.round(rect.x),
                y: Math.round(rect.y),
                width: Math.round(rect.width),
                height: Math.round(rect.height)
            },
            is_header: isHeaderElement(el),
            timestamp: Date.now()
        };
    }

    // ============================================================
    // 事件处理
    // ============================================================

    let currentHoverEl = null;

    /**
     * 鼠标悬停处理
     */
    function handleMouseOver(e) {
        if (!window.weaver_pick_mode) return;

        const el = e.target;

        // 使用宽松检测，让更多元素可高亮
        if (!isInteractiveElement(el)) return;

        // 移除之前的高亮
        if (currentHoverEl && currentHoverEl !== el) {
            currentHoverEl.classList.remove('weaver-hover');
        }

        el.classList.add('weaver-hover');
        currentHoverEl = el;
    }

    /**
     * 鼠标离开处理
     */
    function handleMouseOut(e) {
        const el = e.target;
        el.classList.remove('weaver-hover');

        if (currentHoverEl === el) {
            currentHoverEl = null;
        }
    }

    /**
     * 双击处理 - 只处理输入框，自动检测同级元素
     */
    function handleDoubleClick(e) {
        if (!window.weaver_pick_mode) return;

        const el = e.target;

        // 只处理输入元素（不处理表头）
        if (!isInputElement(el)) return;

        // 阻止默认行为和事件冒泡
        e.preventDefault();
        e.stopPropagation();

        // 收集元素信息
        const fingerprint = collectFingerprint(el);

        // 查找父级标题文本（用作显示名称）
        const parentHeader = findParentHeaderText(el);
        fingerprint.parent_header = parentHeader;

        // 如果有父级标题，用它替代 label_text
        if (parentHeader) {
            fingerprint.label_text = parentHeader;
        }

        // 查找同级输入框
        const siblings = findSiblingInputs(el);
        fingerprint.sibling_count = siblings.length;
        fingerprint.has_siblings = siblings.length >= 2;

        // 如果有同级元素，记录它们的信息（供后续批量选择使用）
        if (siblings.length >= 2) {
            fingerprint.sibling_inputs = siblings.map(inp => ({
                xpath: getXPath(inp),
                css_selector: getCssSelector(inp),
                element_id: inp.id || '',
                placeholder: inp.placeholder || ''
            }));
        }

        // 闪烁选中的元素
        flashElement(el);

        // 存储到全局变量，供 Python 轮询
        window.weaver_picked_element = fingerprint;

        console.log('[Weaver] Input picked:', fingerprint);
    }

    /**
     * 元素闪烁效果
     */
    function flashElement(el) {
        if (!el) return;

        el.classList.add('weaver-flash');

        // 动画结束后移除类
        setTimeout(() => {
            el.classList.remove('weaver-flash');
        }, 900);  // 0.3s * 3 次
    }

    // ============================================================
    // 公开 API（供 Python 调用）
    // ============================================================

    /**
     * 批量闪烁元素 - 使用包围框模式（性能优化版）
     * 
     * 不再逐个闪烁 100 个元素，而是计算所有元素的包围框，
     * 创建一个覆盖整个区域的闪烁框，更清晰且性能更好。
     * 
     * @param {string[]} xpaths - XPath 数组
     */
    window.weaver_flash_elements = function (xpaths) {
        if (!xpaths || xpaths.length === 0) return;

        // 收集所有元素的边界
        let minX = Infinity, minY = Infinity;
        let maxX = -Infinity, maxY = -Infinity;
        let foundCount = 0;

        xpaths.forEach(xpath => {
            try {
                const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                const el = result.singleNodeValue;
                if (el) {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        minX = Math.min(minX, rect.left);
                        minY = Math.min(minY, rect.top);
                        maxX = Math.max(maxX, rect.right);
                        maxY = Math.max(maxY, rect.bottom);
                        foundCount++;
                    }
                }
            } catch (err) {
                // 忽略无效的 XPath
            }
        });

        // 如果没有找到任何元素，退出
        if (foundCount === 0) return;

        // 添加一些内边距
        const padding = 4;
        minX = Math.max(0, minX - padding);
        minY = Math.max(0, minY - padding);
        maxX = Math.min(window.innerWidth, maxX + padding);
        maxY = Math.min(window.innerHeight, maxY + padding);

        // 创建包围框覆盖层
        const overlayId = 'weaver-bounding-flash';
        let overlay = document.getElementById(overlayId);

        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = overlayId;
            overlay.style.cssText = `
                position: fixed;
                pointer-events: none;
                z-index: 999998;
                border: 3px solid #000000;
                border-radius: 4px;
                background: rgba(0, 0, 0, 0.08);
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
                transition: opacity 0.15s ease;
            `;
            document.body.appendChild(overlay);
        }

        // 设置位置和大小
        overlay.style.left = minX + 'px';
        overlay.style.top = minY + 'px';
        overlay.style.width = (maxX - minX) + 'px';
        overlay.style.height = (maxY - minY) + 'px';
        overlay.style.opacity = '1';

        // 显示数量提示（如果超过 1 个元素）
        if (foundCount > 1) {
            overlay.innerHTML = `<span style="
                position: absolute;
                top: -24px;
                left: 0;
                background: #000;
                color: #fff;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-family: sans-serif;
            ">📦 ${foundCount} 个输入框</span>`;
        } else {
            overlay.innerHTML = '';
        }

        // 闪烁 3 次后隐藏
        let flashCount = 0;
        const flashInterval = setInterval(() => {
            flashCount++;
            overlay.style.opacity = (flashCount % 2 === 0) ? '1' : '0.3';

            if (flashCount >= 6) { // 3 次闪烁 = 6 次切换
                clearInterval(flashInterval);
                overlay.style.opacity = '0';
                setTimeout(() => {
                    overlay.innerHTML = '';
                }, 200);
            }
        }, 150);
    };

    /**
     * 获取并清除已选择的元素
     */
    window.weaver_get_and_clear_picked = function () {
        const picked = window.weaver_picked_element;
        window.weaver_picked_element = null;
        return picked;
    };

    /**
     * 开启/关闭选择模式
     */
    window.weaver_set_pick_mode = function (enabled) {
        window.weaver_pick_mode = !!enabled;
        console.log('[Weaver] Pick mode:', window.weaver_pick_mode);
    };

    // ============================================================
    // 注册事件监听
    // ============================================================

    document.addEventListener('mouseover', handleMouseOver, true);
    document.addEventListener('mouseout', handleMouseOut, true);
    document.addEventListener('dblclick', handleDoubleClick, true);

    // 显示 "Weaver Ready" 指示器 (调试用，确认注入成功)
    const indicatorId = 'weaver-ready-indicator';
    if (!document.getElementById(indicatorId)) {
        const indicator = document.createElement('div');
        indicator.id = indicatorId;
        indicator.style.cssText = `
            position: fixed;
            bottom: 10px;
            right: 10px;
            width: 10px;
            height: 10px;
            background-color: #4CAF50;
            border-radius: 50%;
            z-index: 999999;
            pointer-events: none;
            box-shadow: 0 0 5px rgba(0,0,0,0.5);
            opacity: 0.8;
        `;
        document.body.appendChild(indicator);
    }

    console.log('[Weaver] Interaction script loaded successfully.');

})();
