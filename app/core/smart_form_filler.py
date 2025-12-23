"""
智能表单填充器 - 自愈机制 + 数据转换

参考：UiPath、Automation Anywhere 的 Self-healing

重构说明:
- Element UI 专用方法已提取到 app.core.filler.element_ui_adapter
- 本模块保留核心填充逻辑和自愈机制
"""
import time
from typing import Any, Dict, Optional, Callable

from app.core.smart_form_analyzer import SmartFormAnalyzer
from app.core.filler.element_ui_adapter import ElementUIAdapter


class SmartFormFiller:
    """智能表单填充器（带自愈能力）"""
    
    # Element UI 适配器代理方法
    fill_element_ui_input = staticmethod(ElementUIAdapter.fill_by_placeholder)
    fill_element_ui_by_label = staticmethod(ElementUIAdapter.fill_by_label)
    
    @staticmethod
    def _wait_for_loading_complete(tab, timeout=5):
        """
        等待 Element UI / Ant Design 加载完成
        
        检测常见 UI 框架的加载遮罩，等待其消失后再继续操作。
        这对于有异步数据加载的页面非常重要。
        
        Args:
            tab: DrissionPage 的 tab 对象
            timeout: 最大等待时间（秒），默认5秒
            
        Returns:
            bool: True 表示加载完成，False 表示超时
        """
        start = time.time()
        check_count = 0
        
        while time.time() - start < timeout:
            try:
                js_check = """
                (function() {
                    // Element UI 加载遮罩
                    const elLoading = document.querySelector('.el-loading-mask');
                    if (elLoading && elLoading.offsetParent !== null) {
                        const style = window.getComputedStyle(elLoading);
                        if (style.display !== 'none' && style.visibility !== 'hidden') {
                            return { loading: true, type: 'el-loading-mask' };
                        }
                    }
                    
                    // Ant Design 旋转加载
                    const antSpin = document.querySelector('.ant-spin-spinning');
                    if (antSpin && antSpin.offsetParent !== null) {
                        return { loading: true, type: 'ant-spin' };
                    }
                    
                    // Ant Design 模糊遮罩
                    const antBlur = document.querySelector('.ant-spin-container.ant-spin-blur');
                    if (antBlur) {
                        return { loading: true, type: 'ant-spin-blur' };
                    }
                    
                    // iView/View UI
                    const ivuSpin = document.querySelector('.ivu-spin-fix');
                    if (ivuSpin && ivuSpin.offsetParent !== null) {
                        return { loading: true, type: 'ivu-spin' };
                    }
                    
                    // 通用 loading 类
                    const genericLoading = document.querySelector('[class*="loading"]:not(input):not(button)');
                    if (genericLoading && genericLoading.offsetParent !== null) {
                        const style = window.getComputedStyle(genericLoading);
                        if (style.display !== 'none' && style.opacity !== '0') {
                            // 排除小型 loading 图标
                            const rect = genericLoading.getBoundingClientRect();
                            if (rect.width > 100 && rect.height > 100) {
                                return { loading: true, type: 'generic' };
                            }
                        }
                    }
                    
                    return { loading: false };
                })();
                """
                
                result = tab.run_js(js_check)
                
                if result and isinstance(result, dict):
                    if not result.get('loading'):
                        if check_count > 0:
                            print(f"   ✅ 加载完成，耗时 {time.time() - start:.1f}s")
                        return True
                    else:
                        if check_count == 0:
                            print(f"   ⏳ 检测到加载动画: {result.get('type')}, 等待中...")
                        check_count += 1
                        
            except Exception as e:
                pass
            
            time.sleep(0.3)
        
        print(f"   ⚠️ 等待加载超时 ({timeout}s)")
        return False

    
    @staticmethod
    def fill_form_with_healing(tab, excel_data, fingerprint_mappings, 
                               fill_mode='single_form', key_column=None, progress_callback=None):
        """
        自愈式表单填写
        
        Args:
            tab: DrissionPage的tab对象
            excel_data: pandas DataFrame
            fingerprint_mappings: dict {excel_col: ElementFingerprint对象}
            fill_mode: 'single_form' (单据模式) 或 'batch_table' (表格模式)
            key_column: 锚点列名 (仅用于表格模式)
            progress_callback: 进度回调
            
        Returns:
            dict: 填写结果统计
        """
        total_rows = len(excel_data)
        success_count = 0
        error_count = 0
        errors = []
        healed_count = 0
        
        print(f"\n=== 🚀 启动智能填表 (模式: {fill_mode}, 锚点: {key_column}) ===")
        print(f"总行数: {total_rows}")
        print(f"映射字段: {len(fingerprint_mappings)}")
        
        # ===== 新增: 等待页面加载完成 =====
        print("⏳ 检测页面加载状态...")
        SmartFormFiller._wait_for_loading_complete(tab, timeout=5)
        
        # --- 锚点模式前置处理: 构建网页行索引 ---
        web_row_map = {} # { "KeyInfo": row_index }
        if fill_mode == 'batch_table' and key_column and key_column in fingerprint_mappings:
            try:
                if progress_callback:
                    progress_callback(0, total_rows, f"🔍 正在扫描锚点列 [{key_column}]...", "info")
                    
                key_fp = fingerprint_mappings[key_column]
                # 获取该列选择器 (假设是 xpath)
                xpath = key_fp.selectors.get('xpath')
                if xpath:
                    import re
                    # 尝试泛化 XPath: .../tr[1]/td[2] -> .../tr/td[2]
                    # 我们需要找到所有同列元素
                    # 简单策略：替换 tr[\d+] 为 tr
                    generic_xpath = re.sub(r'tr\[\d+\]', 'tr', xpath)
                    
                    # 查找所有元素
                    print(f"   正在扫描锚点数据: {generic_xpath}")
                    elements = tab.eles(f'xpath:{generic_xpath}')
                    
                    for idx, ele in enumerate(elements):
                        txt = ele.text.strip()
                        if txt:
                            # 记录: 值 -> 相对行号 (0-based)
                            # 注意: idx 通常对应 row_idx (0, 1, 2...)
                            # 但如果表头也被算进去了，可能需要调整。
                            # 这里的 idx 是相对于 elements 列表的。
                            # get_selector_for_row 需要的是 "相对于第一行(模板行)" 的偏移?
                            # 不，get_selector_for_row 需要的是 "绝对行号" 或 "增量"。
                            # 如果模板是 tr[1]，那么 row_idx=0 对应 tr[1]。
                            # 如果扫描出来的 elements 第一个就是 tr[1]，那么 idx=0 对应 tr[1]。
                            # 应该是匹配的。
                            web_row_map[txt] = idx
                            # print(f"   Found key: {txt} -> row {idx}")
                    
                    print(f"✅ 锚点扫描完成，索引了 {len(web_row_map)} 行数据")
            except Exception as e:
                print(f"❌ 锚点扫描失败: {e}")

        for row_idx, row_data in excel_data.iterrows():
            row_num = row_idx + 1
            
            try:
                if progress_callback:
                    progress_callback(row_num, total_rows, 
                                   f"📝 正在填写第 {row_num}/{total_rows} 行", "info")
                
                print(f"\n--- 填写第 {row_num} 行 ---")
                filled_fields = 0
                
                # --- 锚点匹配逻辑 ---
                target_web_row_idx = row_idx # 默认: 自增行号
                
                if fill_mode == 'batch_table' and key_column:
                    # 获取Excel中的Key值
                    key_val = str(row_data.get(key_column, '')).strip()
                    if key_val in web_row_map:
                        target_web_row_idx = web_row_map[key_val]
                        print(f"   ⚓ 锚点匹配成功: '{key_val}' -> 网页第 {target_web_row_idx+1} 行")
                    else:
                        print(f"   ⚠️ 锚点匹配失败: '{key_val}' 未在网页中找到，跳过此行")
                        if progress_callback:
                             progress_callback(row_num, total_rows, f"⚠️ 未找到关联数据: {key_val}", "warning")
                        errors.append(f"第{row_num}行: 未找到关联数据 '{key_val}'")
                        error_count += 1
                        continue # 跳过此行
                
                attempted_count = 0
                current_row_errors = []
                for excel_col, fingerprint in fingerprint_mappings.items():
                    # 如果是锚点列本身，通常不需要填写（它是用来定位的），或者是只读的
                    if excel_col == key_column:
                        continue
                        
                    try:
                        # 获取Excel值
                        cell_value = row_data[excel_col]
                        # ... (rest of logic)
                        if cell_value is None or (isinstance(cell_value, float) and str(cell_value) == 'nan'):
                            continue
                        
                        cell_value = str(cell_value).strip()
                        if not cell_value:
                            continue
                            
                        # 只要有有效数据，就视为尝试过填充
                        attempted_count += 1
                        
                        # 智能数据转换
                        transformed_value = SmartFormAnalyzer.suggest_data_transformation(
                            cell_value, 
                            fingerprint.features.get('type', '')
                        )
                        
                        # --- 核心逻辑: 选择器处理 ---
                        target_fingerprint = fingerprint
                        use_dynamic_selector = False
                        dynamic_selector = None
                        
                        if fill_mode == 'batch_table':
                            # 表格模式：需要动态计算第N行的选择器
                            # row_idx=0 -> no offset (Row 1)
                            # row_idx=1 -> offset + 1 (Row 2)
                            
                            # 尝试生成动态选择器
                            # 我们假设映射的是第1行，所以 offset = row_idx
                            dyn_sel = fingerprint.get_selector_for_row(target_web_row_idx)
                            if dyn_sel:
                                use_dynamic_selector = True
                                dynamic_selector = dyn_sel
                            else:
                                # 如果无法生成动态选择器（例如不是表格行），则回退到原始指纹
                                # 但如果你在填第2行，却用了第1行的元素，就会覆盖。
                                # 这种情况下应该报警，但为了兼容性，先继续
                                pass
                        
                        # 执行填充
                        success = False
                        
                        if use_dynamic_selector:
                            # 动态选择器模式
                            sel_type, sel_str = dynamic_selector
                            try:
                                if sel_type == 'xpath':
                                    ele = tab.ele(f'xpath:{sel_str}', timeout=0.5)
                                else:
                                    ele = tab.ele(sel_str, timeout=0.5)
                                    
                                if ele:
                                    ele.clear()
                                    ele.input(transformed_value)
                                    success = True
                            except:
                                success = False
                        else:
                            # 常规/单据模式
                            success = SmartFormFiller._fill_with_fallback(
                                tab, fingerprint, transformed_value
                            )
                        
                        if success:
                            # print(f"  ✓ [{excel_col}] = {transformed_value}") # 简化日志
                            filled_fields += 1
                        else:
                            # 失败处理
                            if fill_mode == 'single_form':
                                # 单据模式才尝试高级自愈，表格模式的自愈太复杂暂时跳过
                                print(f"  ⚠️ 元素定位失败，尝试自愈...")
                                healed = SmartFormFiller._try_heal_and_fill(
                                    tab, fingerprint, transformed_value
                                )
                                if healed:
                                    print(f"  ✅ 自愈成功!")
                                    filled_fields += 1
                                    healed_count += 1
                                else:
                                    raise Exception("自愈失败")
                            else:
                                raise Exception(f"无法定位第{row_num}行的元素")
                        
                    except Exception as e:
                        error_msg = f"字段[{excel_col}] 填写失败: {e}"
                        # 暂存错误
                        current_row_errors.append(f"第{row_num}行: {error_msg}")
                
                if filled_fields == 0:
                    # 关键修改：如果是表格模式，且Excel有数据但无法填充，说明网页行已结束
                    if fill_mode == 'batch_table' and attempted_count > 0:
                         stop_msg = f"⛔ 检测到网页表格行已结束 (第{row_num}行无匹配元素)，停止填充。"
                         print(f"  {stop_msg}")
                         if progress_callback:
                             progress_callback(row_num, total_rows, "✅ 录入完成 (表格行结束)", "success")
                         break # 退出循环，丢弃 current_row_errors
                    
                    msg = f"第 {row_num} 行未能填充任何字段"
                    print(f"  ⚠️ {msg}")
                    # 确认是错误
                    for err in current_row_errors:
                        print(f"  ✗ {err.split(': ', 1)[1]}")
                    errors.extend(current_row_errors)
                    
                    if progress_callback:
                        progress_callback(row_num, total_rows, f"❌ {msg}", "error")
                    error_count += 1
                    continue
                
                # 如果行有效，但有部分字段失败，也记录下来
                if current_row_errors:
                    for err in current_row_errors:
                        print(f"  ✗ {err.split(': ', 1)[1]}")
                    errors.extend(current_row_errors)
                
                print(f"  ✅ 第{row_num}行完成，填充 {filled_fields} 个字段")
                
                # 行后操作
                if fill_mode == 'single_form' and row_num < total_rows:
                    # 单据模式：通常填完一行需要提交，然后进入下一张单据
                    # 这里暂时简单等待，用户需要手动提交或我们无法自动化提交
                    # 更好的方式是：填完 -> 提示用户/等待 -> 循环
                    # 但根据用户要求，单据模式 = 行由行填 (Submit -> Next)
                    # 鉴于没有配置 Submit 按钮的地方，我们只能 Wait
                    pass
                
                success_count += 1
                
                if progress_callback:
                    progress_callback(row_num, total_rows,
                                   f"✅ 第 {row_num}/{total_rows} 行完成", "success")
                
            except Exception as e:
                error_count += 1
                error_msg = f"第{row_num}行严重错误: {e}"
                print(f"❌ {error_msg}")
                errors.append(error_msg)
                
                if progress_callback:
                    progress_callback(row_num, total_rows,
                                   f"❌ {error_msg}", "error")
        
        result = {
            'total': total_rows,
            'success': success_count,
            'error': error_count,
            'healed': healed_count,
            'errors': errors
        }
        
        print(f"\n=== 填表完成 ===")
        print(f"成功: {success_count}/{total_rows}")
        print(f"失败: {error_count}/{total_rows}")
        
        return result
    
    @staticmethod
    def _fill_with_fallback(tab, fingerprint, value):
        """
        使用备用选择器填充（优先级顺序）+ 完整事件模拟
        
        Args:
            tab: tab对象
            fingerprint: 元素指纹
            value: 要填充的值
            
        Returns:
            bool: 是否成功
        """
        # ===== 新增: Iframe 上下文切换（政府级 Vue 站点专用）=====
        in_iframe = False
        frame_path = getattr(fingerprint, 'frame_info', {}).get('frame_path', '')
        
        if frame_path:
            try:
                # 从 frame_path（如 "iframe[0]"）提取索引
                import re
                match = re.search(r'iframe\[(\d+)\]', frame_path)
                if match:
                    frame_index = int(match.group(1))
                    tab.to_frame(frame_index)
                    in_iframe = True
            except Exception as e:
                print(f"   ⚠️ 切换到 iframe 失败: {e}")
        
        try:
            # 获取元素信息
            elem_id = fingerprint.raw_data.get('id', '')
            xpath = fingerprint.selectors.get('xpath', '')
            css_selector = fingerprint.selectors.get('css', '')
            elem_type = fingerprint.features.get('type', 'text')
            tag_name = fingerprint.features.get('tag', 'input')
            
            # 优先使用 JS 事件模拟（更可靠）
            js_result = SmartFormFiller._fill_with_js_events(
                tab, elem_id, xpath, css_selector, str(value), elem_type, tag_name
            )
        
            if js_result:
                return True
            
            # JS 失败时回退到原生方法
            print(f"  ⚠️ JS填充失败，尝试原生方法...")
            
            # 按优先级尝试所有选择器
            for selector_type, selector in fingerprint.get_fallback_selectors():
                try:
                    if selector_type == 'id':
                        elem = tab.ele(selector, timeout=1)
                    elif selector_type == 'xpath':
                        elem = tab.ele(f'xpath:{selector}', timeout=1)
                    elif selector_type == 'css':
                        elem = tab.ele(f'css:{selector}', timeout=1)
                    else:
                        elem = tab.ele(selector, timeout=1)
                    
                    if elem:
                        elem.clear()
                        elem.input(value)
                        return True
                except:
                    continue
            
            return False
            
        finally:
            # ===== 确保切回主框架 =====
            if in_iframe:
                try:
                    tab.to_main()
                except:
                    pass
    
    @staticmethod
    def _fill_with_js_events(tab, elem_id, xpath, css_selector, value, elem_type, tag_name):
        """
        使用 JS 模拟完整用户行为填充元素
        
        行为链: Focus -> Clear -> Set Value -> Input Event -> Change Event -> Blur
        
        Args:
            tab: DrissionPage tab 对象
            elem_id: 元素 ID
            xpath: XPath 选择器
            css_selector: CSS 选择器
            value: 要填充的值
            elem_type: 元素类型 (text/select/checkbox 等)
            tag_name: 标签名 (input/select/textarea)
            
        Returns:
            bool: 是否成功
        """
        # 转义特殊字符
        value_escaped = value.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')
        elem_id_escaped = elem_id.replace("'", "\\'") if elem_id else ''
        xpath_escaped = xpath.replace("'", "\\'").replace('"', '\\"') if xpath else ''
        css_escaped = css_selector.replace("'", "\\'") if css_selector else ''
        
        js_fill = f"""
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
                // ===== 1. Focus 阶段 =====
                el.focus();
                el.dispatchEvent(new FocusEvent('focusin', {{ bubbles: true, cancelable: true }}));
                el.dispatchEvent(new FocusEvent('focus', {{ bubbles: false, cancelable: true }}));
                
                // ===== 2. 清空并设置值 =====
                let tagName = el.tagName.toLowerCase();
                let inputType = (el.type || 'text').toLowerCase();
                
                if (tagName === 'select') {{
                    // 下拉框：尝试按值或文本匹配
                    let matched = false;
                    for (let opt of el.options) {{
                        if (opt.value === '{value_escaped}' || opt.text === '{value_escaped}') {{
                            el.value = opt.value;
                            matched = true;
                            break;
                        }}
                    }}
                    if (!matched && el.options.length > 0) {{
                        // 模糊匹配
                        for (let opt of el.options) {{
                            if (opt.text.includes('{value_escaped}') || '{value_escaped}'.includes(opt.text)) {{
                                el.value = opt.value;
                                matched = true;
                                break;
                            }}
                        }}
                    }}
                }} else if (inputType === 'checkbox' || inputType === 'radio') {{
                    // 复选框/单选框
                    let shouldCheck = '{value_escaped}'.toLowerCase() === 'true' || 
                                     '{value_escaped}' === '1' || 
                                     '{value_escaped}' === '是';
                    if (el.checked !== shouldCheck) {{
                        el.checked = shouldCheck;
                    }}
                }} else {{
                    // 文本输入框 / textarea
                    el.value = '';  // 先清空
                    el.value = '{value_escaped}';
                }}
                
                // ===== 3. 触发 Input 事件 (Vue/React 监听) =====
                el.dispatchEvent(new Event('input', {{ bubbles: true, cancelable: true }}));
                el.dispatchEvent(new InputEvent('input', {{ 
                    bubbles: true, 
                    cancelable: true,
                    data: '{value_escaped}',
                    inputType: 'insertText'
                }}));
                
                // ===== 4. 触发 Change 事件 (验证/级联) =====
                el.dispatchEvent(new Event('change', {{ bubbles: true, cancelable: true }}));
                
                // ===== 5. Blur 阶段 (触发校验) =====
                el.dispatchEvent(new FocusEvent('blur', {{ bubbles: false, cancelable: true }}));
                el.dispatchEvent(new FocusEvent('focusout', {{ bubbles: true, cancelable: true }}));
                el.blur();
                
                return {{ success: true, value: el.value }};
                
            }} catch (e) {{
                return {{ success: false, error: e.toString() }};
            }}
        }})();
        """
        
        try:
            result = tab.run_js(js_fill)
            if result and isinstance(result, dict):
                if result.get('success'):
                    return True
                else:
                    print(f"    JS填充错误: {result.get('error', 'unknown')}")
            return False
        except Exception as e:
            print(f"    JS执行异常: {e}")
            return False
    
    @staticmethod
    def _try_heal_and_fill(tab, fingerprint, value):
        """
        尝试自愈并填充
        
        逻辑：通过语义锚点（label、nearby_text）重新定位元素
        
        Args:
            tab: tab对象
            fingerprint: 元素指纹
            value: 要填充的值
            
        Returns:
            bool: 是否成功
        """
        # 方法1: 通过Label文本定位
        label_text = fingerprint.anchors.get('label')
        if label_text:
            try:
                # 查找包含该文本的label
                js = f"""
                (function() {{
                    const labels = Array.from(document.querySelectorAll('label'));
                    const target = labels.find(l => l.innerText.includes('{label_text}'));
                    if (!target) return null;
                    
                    // 查找关联的input
                    const forId = target.getAttribute('for');
                    if (forId) return document.getElementById(forId);
                    
                    // 查找label内的input
                    return target.querySelector('input, select, textarea');
                }})();
                """
                result = tab.run_js(js)
                if result:
                    # 成功找到，使用新的选择器
                    elem = tab.ele('xpath://input[@id]', timeout=0.5)  # 示例
                    if elem:
                        elem.clear()
                        elem.input(value)
                        return True
            except:
                pass
        
        # 方法2: 通过附近文本定位
        nearby_text = fingerprint.anchors.get('nearby_text')
        if nearby_text:
            try:
                # 查找包含该文本的元素，然后找附近的input
                js = f"""
                (function() {{
                    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
                    let node;
                    while (node = walker.nextNode()) {{
                        if (node.textContent.includes('{nearby_text}')) {{
                            let parent = node.parentElement;
                            let input = parent.querySelector('input, select, textarea');
                            if (!input) {{
                                input = parent.nextElementSibling?.querySelector('input, select, textarea');
                            }}
                            if (input) return input;
                        }}
                    }}
                    return null;
                }})();
                """
                result = tab.run_js(js)
                if result:
                    # 这里简化处理，实际应该返回元素的新选择器
                    return True
            except:
                pass
        
        return False

