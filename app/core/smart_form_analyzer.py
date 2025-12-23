"""
智能表单分析器 Pro - 空间几何 + JS快照模式
版本: 2.0
优化: 
  - 性能: 全量 JS 执行，一次返回所有元素
  - 精度: 视觉坐标匹配（左侧/上方标题）
  - 深度: 表格 row_index、Shadow DOM、自定义控件
"""
from app.core.element_fingerprint import ElementFingerprint


class SmartFormAnalyzer:
    """
    智能表单分析器 Pro
    采用「空间几何 + JS 快照」模式
    """
    
    @staticmethod
    def get_analysis_js():
        """
        获取高性能 JS 分析脚本
        
        从独立的 form_analyzer.js 文件加载脚本。
        该脚本一次执行返回所有可交互元素的完整信息。
        
        功能:
        - 加载状态探测（Ant Design/ElementUI 等）
        - 多重选择器生成（XPath/CSS/ID）
        - 视觉坐标匹配（左侧/上方标题）
        - Shadow DOM 穿透
        - 表格 row_index 识别
        
        Returns:
            JavaScript 代码字符串
        """
        from app.infrastructure.js.script_store import ScriptStore
        return ScriptStore.get_form_analyzer_js()


    @staticmethod
    def deep_scan_page(tab, max_wait=15, poll_interval=0.8):
        """
        深度扫描网页 - JS 快照模式 + 智能稳定性检测
        
        核心机制:
        - 加载探测: 检测 Ant Design/ElementUI 等加载动画
        - 稳定性算法: 连续2次元素数量一致才认为渲染稳定
        - 静默环境: 自动劫持 alert/confirm 防止阻塞
        
        Args:
            tab: DrissionPage 的 tab 对象
            max_wait: 最大等待时间（秒），默认15秒
            poll_interval: 轮询间隔（秒），默认0.8秒
            
        Returns:
            list[ElementFingerprint]: 元素指纹列表
        """
        import time
        
        print("\n=== 🚀 启动 JS 快照扫描（v3.0 稳定性增强模式） ===")
        
        fingerprints = []
        last_count = -1
        stable_count = 0
        best_result = None
        max_polls = int(max_wait / poll_interval)
        
        try:
            for poll_idx in range(max_polls):
                # 执行 JS 扫描脚本
                if poll_idx == 0:
                    print("🔄 正在执行 JS 批量扫描...")
                
                js_result = tab.run_js(SmartFormAnalyzer.get_analysis_js())
                
                # 检查错误
                if isinstance(js_result, dict):
                    if 'error' in js_result:
                        print(f"⚠️ JS 扫描出错: {js_result['error']}")
                        print("🔄 回退到原生扫描模式...")
                        return SmartFormAnalyzer._fallback_native_scan(tab)
                    
                    # 检查加载状态
                    if js_result.get('status') == 'loading':
                        loader = js_result.get('loader', 'unknown')
                        if poll_idx == 0:
                            print(f"⏳ 检测到加载动画: {loader}，等待页面就绪...")
                        time.sleep(poll_interval)
                        continue
                    
                    # 如果返回的是包含 elements 的对象
                    if 'elements' in js_result:
                        js_result = js_result['elements']
                
                if not isinstance(js_result, list):
                    print(f"⚠️ JS 返回格式异常: {type(js_result)}")
                    time.sleep(poll_interval)
                    continue
                
                current_count = len(js_result)
                
                # 稳定性检测
                if current_count == last_count and current_count > 0:
                    stable_count += 1
                    if stable_count >= 3:
                        # 连续3次数量相同，认为稳定
                        print(f"✅ 页面稳定 (连续 {stable_count} 次检测到 {current_count} 个元素)")
                        best_result = js_result
                        break
                else:
                    stable_count = 0
                    if current_count > 0:
                        best_result = js_result  # 保存最新有效结果
                
                last_count = current_count
                
                if poll_idx > 0 and poll_idx % 3 == 0:
                    print(f"   轮询 {poll_idx+1}/{max_polls}: {current_count} 个元素...")
                
                time.sleep(poll_interval)
            
            # 超时或稳定后处理
            if best_result is None or len(best_result) == 0:
                print("⚠️ 未能获取有效元素，尝试回退...")
                return SmartFormAnalyzer._fallback_native_scan(tab)
            
            print(f"📊 JS 扫描完成，发现 {len(best_result)} 个可交互元素")
            
            # 转换为 ElementFingerprint 对象
            for item in best_result:
                try:
                    fp = ElementFingerprint(item)
                    fingerprints.append(fp)
                except Exception as e:
                    # 静默跳过单个元素错误
                    continue
            
            # 统计信息
            table_count = sum(1 for fp in fingerprints if fp.raw_data.get('is_table_cell'))
            visual_count = sum(1 for fp in fingerprints if fp.raw_data.get('visual_label'))
            shadow_count = sum(1 for fp in fingerprints if fp.raw_data.get('shadow_depth', 0) > 0)
            
            print(f"✅ 主文档扫描完成！发现 {len(fingerprints)} 个多维指纹")
            print(f"   表格元素: {table_count} 个")
            print(f"   视觉匹配: {visual_count} 个")
            print(f"   Shadow DOM: {shadow_count} 个")
            
            # ===== 新增: Iframe 递归扫描（政府级 Vue 站点专用） =====
            iframe_fingerprints = SmartFormAnalyzer._scan_iframes(tab)
            if iframe_fingerprints:
                fingerprints.extend(iframe_fingerprints)
                print(f"   📦 Iframe 内元素: {len(iframe_fingerprints)} 个")
            
            print(f"\\n🎯 总计: {len(fingerprints)} 个可操作元素")
            
            return fingerprints
            
        except Exception as e:
            print(f"❌ JS 扫描严重失败: {e}")
            import traceback
            traceback.print_exc()
            print("🔄 尝试回退到原生扫描...")
            return SmartFormAnalyzer._fallback_native_scan(tab)

    @staticmethod
    def _fallback_native_scan(tab):
        """
        回退的原生扫描模式（兼容旧环境）
        """
        print("🔄 正在执行原生扫描（兼容模式）...")
        
        fingerprints = []
        
        try:
            # 获取所有输入元素
            inputs = tab.eles('xpath://input[not(@type="hidden") and not(@type="button") and not(@type="submit") and not(@type="reset") and not(@type="image") and not(@type="file")]')
            selects = tab.eles('tag:select')
            textareas = tab.eles('tag:textarea')
            
            all_uielems = inputs + selects + textareas
            print(f"   发现 {len(all_uielems)} 个可交互元素")
            
            for idx, el in enumerate(all_uielems):
                try:
                    attrs = el.attrs or {}
                    tag = el.tag
                    elem_type = attrs.get('type', tag)
                    elem_name = attrs.get('name', '')
                    elem_id = attrs.get('id', '')
                    placeholder = attrs.get('placeholder', '')
                    
                    found_label = ""
                    
                    # 表格表头分析
                    try:
                        parent_td = el.parent('tag:td')
                        if parent_td:
                            prev_siblings = parent_td.prevs('tag:td')
                            col_index = len(prev_siblings)
                            
                            table = parent_td.parent('tag:table')
                            if table:
                                th = table.ele(f'xpath:.//thead//tr/th[{col_index + 1}]', timeout=0.1)
                                if th:
                                    found_label = th.text.strip()
                                else:
                                    first_row_th = table.ele(f'xpath:.//tr[1]/th[{col_index + 1}]', timeout=0.1)
                                    if first_row_th:
                                        found_label = first_row_th.text.strip()
                                    else:
                                        first_row_td = table.ele(f'xpath:.//tr[1]/td[{col_index + 1}]', timeout=0.1)
                                        if first_row_td:
                                            found_label = first_row_td.text.strip()
                    except:
                        pass
                    
                    # 常规 Label
                    if not found_label and elem_id:
                        try:
                            label_ele = tab.ele(f'tag:label@for={elem_id}', timeout=0.1)
                            if label_ele:
                                found_label = label_ele.text.strip()
                        except:
                            pass
                    
                    if not found_label:
                        found_label = placeholder or elem_name or elem_id
                    
                    data = {
                        'index': idx,
                        'tagName': tag,
                        'type': elem_type,
                        'name': elem_name,
                        'className': attrs.get('class', ''),
                        'placeholder': placeholder,
                        'id': elem_id,
                        'id_selector': f"#{elem_id}" if elem_id else None,
                        'xpath': el.xpath,
                        'label_text': found_label,
                        'nearby_text': found_label,
                        'rect': {'x': 0, 'y': 0, 'width': 10, 'height': 10}
                    }
                    
                    fp = ElementFingerprint(data)
                    fp.raw_element = el
                    fingerprints.append(fp)
                    
                except Exception as e:
                    continue
            
            print(f"✅ 原生扫描完成！共提取 {len(fingerprints)} 个多维指纹")
            return fingerprints
            
        except Exception as e:
            print(f"❌ 原生扫描失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    def auto_fill_with_healing(tab, xpath, value, original_label=None):
        """自愈式填充（保留接口兼容）"""
        pass

    @staticmethod
    def suggest_data_transformation(value, input_type):
        """
        智能数据转换
        Args:
            value: 原始值
            input_type: 目标控件类型 (text, date, checkbox, etc)
        Returns:
            转换后的值
        """
        if value is None:
            return ""
            
        value = str(value).strip()
        
        # 日期处理
        if 'date' in str(input_type).lower():
            if '/' in value:
                return value.replace('/', '-')
            
        return value

    @staticmethod
    def _scan_iframes(tab):
        """
        递归扫描所有 Iframe 内部的元素 (支持多层嵌套)
        
        优化:
        1. 递归穿透: 支持 Main -> Iframe -> Iframe 的嵌套结构
        2. 分级等待: 
           - 业务 Iframe (ifarmedj等): 启用 5s 智能轮询
           - 普通 Iframe: 快速扫描，无元素即退出，避免拖慢整体速度
        3. 使用 DrissionPage 的 get_frame() API 获取 ChromiumFrame 对象
        """
        import time
        
        all_iframe_fingerprints = []
        MAX_DEPTH = 3  # 防止无限递归
        
        def process_frame(frame_obj, depth=0, parent_path=""):
            """递归处理 frame 及其子 frame"""
            nonlocal all_iframe_fingerprints
            
            if depth > MAX_DEPTH:
                print(f"      ⚠️ 达到最大递归深度 {MAX_DEPTH}，停止下探")
                return

            # 1. 扫描当前 Frame 的 Input 元素
            try:
                # 获取当前 Frame 的 URL 判定是否为业务关键 Frame
                try:
                    current_url = frame_obj.url or ""
                except:
                    current_url = ""
                    
                is_business_frame = any(kw in current_url.lower() for kw in [
                    'ifarmedj', 'tps-local', 'trade', 'record', 'invoice', 'form', 'entry'
                ])
                
                # 策略: 业务 Frame 多给点耐心，普通 Frame 快速略过
                max_retries = 5 if is_business_frame else 1
                poll_interval = 1.0 if is_business_frame else 0.2
                
                found_elements = []
                stable_count = 0
                last_count = -1
                
                for i in range(max_retries):
                    # 在 frame 对象上执行 JS
                    js_result = frame_obj.run_js(SmartFormAnalyzer.get_analysis_js())
                    
                    # 处理 Loading
                    if isinstance(js_result, dict) and js_result.get('status') == 'loading':
                        if is_business_frame: 
                            time.sleep(poll_interval)
                            continue
                        else:
                            break  # 普通 frame 加载中直接跳过
                            
                    # 获取结果
                    current_batch = []
                    if isinstance(js_result, dict) and 'elements' in js_result:
                        current_batch = js_result['elements']
                    elif isinstance(js_result, list):
                        current_batch = js_result
                        
                    curr_count = len(current_batch)
                    
                    if curr_count > 0:
                        if curr_count == last_count:
                            stable_count += 1
                        else:
                            stable_count = 0
                        
                        last_count = curr_count
                        
                        # 只要有数据，且普通frame或业务frame稳定了，就采用
                        if not is_business_frame or stable_count >= 1:
                            found_elements = current_batch
                            if is_business_frame:
                                print(f"      ✅ [深度{depth}] 业务Frame捕获: {curr_count} 个元素")
                            break
                    
                    if i < max_retries - 1:
                        time.sleep(poll_interval)

                # 保存当前层结果
                if found_elements:
                    for item in found_elements:
                        item['frame_path'] = f"{parent_path}"
                        item['in_iframe'] = True
                        item['frame_depth'] = depth
                        try:
                            all_iframe_fingerprints.append(ElementFingerprint(item))
                        except: 
                            pass
                            
            except Exception as e:
                print(f"      ⚠️ Frame扫描异常: {e}")

            # 2. 递归寻找子 Iframes
            try:
                # 在当前 frame 对象上查找子 iframe
                child_iframes = frame_obj.eles('tag:iframe')
                
                if child_iframes and len(child_iframes) > 0:
                    print(f"      ↳ [深度{depth}] 发现 {len(child_iframes)} 个子 Iframe，准备递归...")
                    
                    for i, child_frame_ele in enumerate(child_iframes):
                        try:
                            # 获取一些元数据用于日志
                            src = child_frame_ele.attr('src') or ''
                            
                            # 过滤过小的 iframe
                            try:
                                rect = child_frame_ele.rect
                                if rect.get('width', 0) < 50 or rect.get('height', 0) < 50:
                                    continue
                            except:
                                pass
                            
                            # 使用 DrissionPage 的 get_frame() 获取 ChromiumFrame 对象
                            child_frame_obj = frame_obj.get_frame(child_frame_ele)
                            
                            if child_frame_obj:
                                # 递归调用
                                new_path = f"{parent_path}iframe[{i}]->" if parent_path else f"iframe[{i}]->"
                                process_frame(child_frame_obj, depth + 1, new_path)
                            
                        except Exception as e:
                            print(f"      ❌ 递归子Frame[{i}]失败: {e}")
                            
            except Exception as e:
                # 可能是跨域 iframe
                pass

        # === 主入口 ===
        try:
            print(f"\\n📦 开始递归 Iframe 扫描...")
            
            # 获取顶层 iframe 元素
            try:
                top_iframe_elements = tab.eles('tag:iframe')
            except:
                top_iframe_elements = []
            
            if not top_iframe_elements or len(top_iframe_elements) == 0:
                print("   未检测到 Iframe")
                return []

            print(f"   检测到 {len(top_iframe_elements)} 个顶层 Iframe")
            
            for i, frame_ele in enumerate(top_iframe_elements):
                try:
                    src = frame_ele.attr('src') or ''
                    
                    # 过滤过小的 iframe
                    try:
                        rect = frame_ele.rect
                        if rect.get('width', 0) < 50 or rect.get('height', 0) < 50:
                            continue
                    except:
                        pass
                    
                    is_business = any(kw in src.lower() for kw in [
                        'ifarmedj', 'tps-local', 'trade', 'record', 'invoice', 'form', 'entry'
                    ])
                    
                    frame_desc = src.split('?')[0].split('/')[-1][:30] if src else f'[{i}]'
                    print(f"\\n   🔍 顶层 Iframe[{i}]: {frame_desc}{'  ⭐业务' if is_business else ''}")
                    
                    # 使用 DrissionPage 的 get_frame() 获取 ChromiumFrame 对象
                    frame_obj = tab.get_frame(frame_ele)
                    
                    if frame_obj:
                        process_frame(frame_obj, depth=1, parent_path=f"iframe[{i}]")
                    else:
                        print(f"      ⚠️ 无法获取 frame 对象")
                        
                except Exception as e:
                    print(f"   ⚠️ 顶层 Iframe[{i}] 无法进入: {e}")
                    
            print(f"\\n🎯 Iframe 递归扫描完成，共获取 {len(all_iframe_fingerprints)} 个元素")
            return all_iframe_fingerprints
            
        except Exception as e:
            print(f"❌ 递归扫描总控失败: {e}")
            import traceback
            traceback.print_exc()
            return []


