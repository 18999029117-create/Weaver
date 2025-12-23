import json

class CoordinateMapper:
    """处理全局屏幕坐标到浏览器视口坐标的精确转换"""
    
    @staticmethod
    def screen_to_viewport(tab, screen_x, screen_y, app_width=None):
        """
        将全局屏幕坐标转换为浏览器视口坐标
        
        由于我们控制了浏览器的位置（75% 分屏），可以直接计算
        
        Args:
            tab: DrissionPage 的 tab 对象
            screen_x: 鼠标释放时的全局屏幕 X 坐标
            screen_y: 鼠标释放时的全局屏幕 Y 坐标
            app_width: 应用窗口宽度（屏幕的 25%）
            
        Returns:
            tuple: (viewport_x, viewport_y) 视口内的坐标
        """
        try:
            print(f"\n=== 坐标转换调试（简化版） ===")
            print(f"输入: 屏幕坐标 ({screen_x}, {screen_y})")
            
            # 如果没有传入 app_width，尝试从 tab 获取
            if app_width is None:
                try:
                    # 尝试用 JS 获获取屏幕宽度并计算 app_width
                    screen_width = tab.run_js("screen.width")
                    if screen_width:
                        app_width = int(screen_width * 0.25)
                        print(f"计算得到应用宽度: {app_width}px")
                except:
                    # 使用默认值（1920 分辨率的 25%）
                    app_width = 480
                    print(f"使用默认应用宽度: {app_width}px")
            
            # 浏览器窗口在屏幕右侧 75%，从 app_width 开始
            browser_left = app_width
            browser_top = 0  # 我们设置的浏览器在顶部
            
            print(f"浏览器左边界: {browser_left}px")
            
            # 估算浏览器 UI 高度（工具栏、地址栏等，一般 70-120px）
            # 可以尝试从 JS 获取，失败则使用估计值
            try:
                ui_height = tab.run_js("window.outerHeight - window.innerHeight")
                if ui_height is None or ui_height < 0:
                    ui_height = 90  # 默认值
            except:
                ui_height = 90
            
            print(f"浏览器 UI 高度（估算）: {ui_height}px")
            
            # 计算视口坐标
            viewport_x = screen_x - browser_left
            viewport_y = screen_y - (browser_top + ui_height)
            
            print(f"计算结果: 视口坐标 ({viewport_x}, {viewport_y})")
            
            # 验证坐标有效性
            if viewport_x < 0:
                print(f"❌ X 坐标为负，鼠标可能在软件窗口内（而非浏览器）")
                return None, None
            
            if viewport_y < 0:
                print(f"❌ Y 坐标为负，鼠标可能在浏览器工具栏上")
                return None, None
            
            print(f"✅ 转换成功\n")
            return viewport_x, viewport_y
            
        except Exception as e:
            print(f"❌ 坐标转换异常: {e}")
            import traceback
            traceback.print_exc()
            return None, None
    
    @staticmethod
    def get_element_at_position(tab, viewport_x, viewport_y):
        """
        使用 DrissionPage 递归检测元素，支持 Shadow DOM 和 Iframe
        
        Args:
            tab: DrissionPage 的 tab 对象
            viewport_x: 视口 X 坐标
            viewport_y: 视口 Y 坐标
            
        Returns:
            dict: 元素信息
        """
        try:
            print(f"\n=== 智能元素检测 ===")
            print(f"坐标: ({viewport_x}, {viewport_y})")
            
            all_inputs = []
            
            # 1. 主文档input
            try:
                inputs = tab.eles('tag:input')
                all_inputs.extend([('main', inp) for inp in inputs])
                print(f"主文档: {len(inputs)} 个input")
            except: pass
            
            # 2. 检测所有iframe中的input
            try:
                iframes = tab.eles('tag:iframe')
                for idx, iframe in enumerate(iframes):
                    try:
                        iframe_inputs = iframe.eles('tag:input', timeout=0.5)
                        all_inputs.extend([(f'iframe{idx}', inp) for inp in iframe_inputs])
                        print(f"iframe{idx}: {len(iframe_inputs)} 个input")
                    except: continue
            except: pass
            
            # 3. 检测Shadow DOM（DrissionPage 4.x 支持）
            try:
                shadow_hosts = tab.eles('css:[shadowroot]', timeout=0.5)
                for idx, host in enumerate(shadow_hosts):
                    try:
                        shadow_inputs = host.shadow_root.eles('tag:input', timeout=0.5)
                        all_inputs.extend([(f'shadow{idx}', inp) for inp in shadow_inputs])
                        print(f"shadow{idx}: {len(shadow_inputs)} 个input")
                    except: continue
            except: pass
            
            # 4. textarea和select
            try:
                textareas = tab.eles('tag:textarea')
                selects = tab.eles('tag:select')
                all_inputs.extend([('main', ta) for ta in textareas])
                all_inputs.extend([('main', sel) for sel in selects])
                print(f"其他: {len(textareas)}个textarea, {len(selects)}个select")
            except: pass
            
            print(f"总计: {len(all_inputs)} 个可输入元素")
            
            if not all_inputs:
                print("❌ 未找到任何输入元素")
                return None
            
            # 5. 计算距离并排序（带性能优化）
            candidates = []
            checked = 0
            
            for source, elem in all_inputs:
                try:
                    rect = elem.rect
                    if not rect:
                        continue
                    
                    x = rect.location.get('x', 0)
                    y = rect.location.get('y', 0)
                    w = rect.size.get('width', 0)
                    h = rect.size.get('height', 0)
                    
                    # 快速过滤：如果元素距离太远，跳过
                    if abs(x - viewport_x) > 500 and abs(y - viewport_y) > 500:
                        continue
                    
                    # 检查点是否在元素矩形内
                    if x <= viewport_x <= x + w and y <= viewport_y <= y + h:
                        distance = 0  # 直接命中
                    else:
                        # 计算到矩形的最短距离
                        dx = max(x - viewport_x, 0, viewport_x - (x + w))
                        dy = max(y - viewport_y, 0, viewport_y - (y + h))
                        distance = (dx**2 + dy**2)**0.5
                    
                    candidates.append({
                        'source': source,
                        'element': elem,
                        'distance': distance,
                        'rect': (x, y, w, h)
                    })
                    
                    checked += 1
                    # 每检查10个元素，检查是否已经找到距离为0的（直接命中）
                    if checked % 10 == 0 and any(c['distance'] == 0 for c in candidates):
                        print(f"已找到直接命中元素，停止搜索")
                        break
                        
                except:
                    continue
            
            print(f"实际检查了 {checked} 个元素")
            
            if not candidates:
                print("❌ 无法获取元素位置信息")
                return None
            
            # 6. 选择最近的元素
            candidates.sort(key=lambda x: x['distance'])
            best = candidates[0]
            
            print(f"最佳匹配: {best['source']}, 距离={best['distance']:.1f}px")
            
            # 如果距离太远（超过300px），提示用户
            if best['distance'] > 300:
                print(f"⚠️ 最近元素距离 {best['distance']:.0f}px，可能不准确")
            
            # 7. 提取元素信息
            elem = best['element']
            attrs = elem.attrs or {}
            
            element_data = {
                'nodeId': None,
                'nodeName': elem.tag.lower(),
                'nodeType': 1,
                'attributes': attrs,
                'backendNodeId': None,
                '_dp_element': elem,
                '_source': best['source']
            }
            
            name = attrs.get('name', attrs.get('id', '未命名'))
            print(f"✅ <{elem.tag}> {name}")
            
            return element_data
            
        except Exception as e:
            print(f"❌ 异常: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def _parse_attributes(attr_list):
        """将 CDP 返回的属性列表转换为字典"""
        if not attr_list:
            return {}
        
        # CDP 返回的属性是 [name1, value1, name2, value2, ...] 格式
        attrs = {}
        for i in range(0, len(attr_list), 2):
            if i + 1 < len(attr_list):
                attrs[attr_list[i]] = attr_list[i + 1]
        return attrs
    
    @staticmethod
    def is_valid_input_element(element_data):
        """
        判断元素是否是有效的可输入元素
        
        Args:
            element_data: get_element_at_position 返回的元素数据
            
        Returns:
            bool: 是否是有效的输入元素
        """
        if not element_data:
            return False
        
        node_name = element_data.get('nodeName', '').lower()
        attributes = element_data.get('attributes', {})
        
        # 检查是否是 input、textarea 或 select
        if node_name in ['input', 'textarea', 'select']:
            # 排除不可编辑的 input 类型
            input_type = attributes.get('type', 'text').lower()
            excluded_types = ['button', 'submit', 'reset', 'image', 'hidden', 'checkbox', 'radio']
            
            if node_name == 'input' and input_type in excluded_types:
                return False
            
            return True
        
        # 检查是否是 contenteditable 元素
        if attributes.get('contenteditable', '').lower() == 'true':
            return True
        
        return False
    
    @staticmethod
    def get_element_identifier(element_data):
        """
        为元素生成唯一标识符（用于映射配置）
        
        Returns:
            str: 元素的唯一标识符
        """
        if not element_data:
            return None
        
        attrs = element_data.get('attributes', {})
        
        # 优先使用 id
        if 'id' in attrs and attrs['id']:
            return f"#{attrs['id']}"
        
        # 其次使用 name
        if 'name' in attrs and attrs['name']:
            return f"[name='{attrs['name']}']"
        
        # 使用 backendNodeId 作为最后的标识
        backend_id = element_data.get('backendNodeId')
        if backend_id:
            return f"backend:{backend_id}"
        
        return None
