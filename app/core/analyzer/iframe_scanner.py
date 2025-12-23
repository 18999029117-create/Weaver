"""
Iframe 扫描器模块

负责递归扫描嵌套 Iframe 中的元素。
支持多层嵌套和分级等待策略。

主要功能:
- 检测页面中的所有 Iframe
- 递归进入每层 Iframe 扫描元素
- 分级等待（业务 Iframe 5s，普通 Iframe 快速跳过）
- 使用 DrissionPage 的 get_frame() API
"""

from typing import List, Dict, Any, Optional, TYPE_CHECKING
import time

if TYPE_CHECKING:
    from ..fingerprint import ElementFingerprint


class IframeScanner:
    """
    Iframe 递归扫描器
    
    支持多层嵌套 Iframe 的递归扫描，
    使用分级等待策略平衡扫描深度和速度。
    """
    
    # 配置参数
    MAX_DEPTH = 3                    # 最大递归深度
    BUSINESS_KEYWORDS = [            # 业务 Iframe 关键词
        'ifarmedj', 'tps-local', 'trade', 'record', 
        'invoice', 'form', 'entry', 'business'
    ]
    BUSINESS_MAX_RETRIES = 5         # 业务 Iframe 最大重试次数
    BUSINESS_POLL_INTERVAL = 1.0     # 业务 Iframe 轮询间隔
    NORMAL_MAX_RETRIES = 1           # 普通 Iframe 重试次数
    NORMAL_POLL_INTERVAL = 0.2       # 普通 Iframe 轮询间隔
    MIN_IFRAME_SIZE = 50             # 最小 Iframe 尺寸（过滤隐藏的）
    
    @classmethod
    def scan_iframes(cls, tab) -> List['ElementFingerprint']:
        """
        递归扫描所有 Iframe 内部的元素
        
        Args:
            tab: DrissionPage 的 tab 对象
            
        Returns:
            所有 Iframe 内元素的 ElementFingerprint 列表
        """
        from ..fingerprint import ElementFingerprint
        from ...utils.js_store import PAGE_SCANNER_JS
        
        all_fingerprints: List[ElementFingerprint] = []
        
        def is_business_frame(url: str) -> bool:
            """判断是否为业务关键 Iframe"""
            return any(kw in url.lower() for kw in cls.BUSINESS_KEYWORDS)
        
        def scan_frame_elements(frame_obj, is_business: bool) -> List[Dict[str, Any]]:
            """扫描单个 Frame 内的元素（含轮询等待）"""
            max_retries = cls.BUSINESS_MAX_RETRIES if is_business else cls.NORMAL_MAX_RETRIES
            poll_interval = cls.BUSINESS_POLL_INTERVAL if is_business else cls.NORMAL_POLL_INTERVAL
            
            found_elements = []
            stable_count = 0
            last_count = -1
            
            for i in range(max_retries):
                try:
                    js_result = frame_obj.run_js(PAGE_SCANNER_JS)
                    
                    # 处理加载状态
                    if isinstance(js_result, dict) and js_result.get('status') == 'loading':
                        if is_business:
                            time.sleep(poll_interval)
                            continue
                        else:
                            break  # 普通 Frame 不等待
                    
                    # 提取元素
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
                        
                        # 稳定性判定
                        if not is_business or stable_count >= 1:
                            found_elements = current_batch
                            if is_business:
                                print(f"      ✅ 业务Frame捕获: {curr_count} 个元素")
                            break
                    
                    if i < max_retries - 1:
                        time.sleep(poll_interval)
                        
                except Exception as e:
                    break
            
            return found_elements
        
        def process_frame(frame_obj, depth: int = 0, parent_path: str = ""):
            """递归处理 Frame 及其子 Frame"""
            nonlocal all_fingerprints
            
            if depth > cls.MAX_DEPTH:
                print(f"      ⚠️ 达到最大递归深度 {cls.MAX_DEPTH}")
                return
            
            # 获取 Frame URL 判断类型
            try:
                current_url = frame_obj.url or ""
            except:
                current_url = ""
            
            is_business = is_business_frame(current_url)
            
            # 扫描当前 Frame 元素
            found_elements = scan_frame_elements(frame_obj, is_business)
            
            if found_elements:
                for item in found_elements:
                    item['frame_path'] = parent_path
                    item['in_iframe'] = True
                    item['frame_depth'] = depth
                    try:
                        all_fingerprints.append(ElementFingerprint(item))
                    except:
                        pass
            
            # 查找子 Iframe 递归
            try:
                child_iframes = frame_obj.eles('tag:iframe')
                if child_iframes:
                    print(f"      ↳ [深度{depth}] 发现 {len(child_iframes)} 个子 Iframe")
                    
                    for i, child_ele in enumerate(child_iframes):
                        try:
                            # 过滤过小的 Iframe
                            try:
                                rect = child_ele.rect
                                if rect.get('width', 0) < cls.MIN_IFRAME_SIZE or \
                                   rect.get('height', 0) < cls.MIN_IFRAME_SIZE:
                                    continue
                            except:
                                pass
                            
                            # 获取子 Frame 对象
                            child_frame = frame_obj.get_frame(child_ele)
                            if child_frame:
                                new_path = f"{parent_path}iframe[{i}]->" if parent_path else f"iframe[{i}]->"
                                process_frame(child_frame, depth + 1, new_path)
                                
                        except Exception as e:
                            print(f"      ❌ 子Frame[{i}]失败: {e}")
                            
            except:
                pass  # 跨域 Iframe 无法访问
        
        # 主入口
        try:
            print(f"\\n📦 开始递归 Iframe 扫描...")
            
            # 获取顶层 Iframe
            try:
                top_iframes = tab.eles('tag:iframe')
            except:
                top_iframes = []
            
            if not top_iframes:
                print("   未检测到 Iframe")
                return []
            
            print(f"   检测到 {len(top_iframes)} 个顶层 Iframe")
            
            for i, frame_ele in enumerate(top_iframes):
                try:
                    src = frame_ele.attr('src') or ''
                    
                    # 过滤过小的 Iframe
                    try:
                        rect = frame_ele.rect
                        if rect.get('width', 0) < cls.MIN_IFRAME_SIZE or \
                           rect.get('height', 0) < cls.MIN_IFRAME_SIZE:
                            continue
                    except:
                        pass
                    
                    is_business = is_business_frame(src)
                    frame_desc = src.split('?')[0].split('/')[-1][:30] if src else f'[{i}]'
                    print(f"\\n   🔍 顶层 Iframe[{i}]: {frame_desc}{'  ⭐业务' if is_business else ''}")
                    
                    # 获取 Frame 对象
                    frame_obj = tab.get_frame(frame_ele)
                    if frame_obj:
                        process_frame(frame_obj, depth=1, parent_path=f"iframe[{i}]")
                    else:
                        print(f"      ⚠️ 无法获取 frame 对象")
                        
                except Exception as e:
                    print(f"   ⚠️ 顶层 Iframe[{i}] 失败: {e}")
            
            print(f"\\n🎯 Iframe 递归扫描完成，共获取 {len(all_fingerprints)} 个元素")
            return all_fingerprints
            
        except Exception as e:
            print(f"❌ Iframe 扫描异常: {e}")
            import traceback
            traceback.print_exc()
            return []
