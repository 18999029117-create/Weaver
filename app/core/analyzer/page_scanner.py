"""
页面扫描器模块

负责扫描页面中的可交互元素（input、select、textarea 等）。
使用 JavaScript 注入方式一次性获取所有元素信息。

主要功能:
- 执行 JS 快照扫描
- 稳定性检测（轮询直到元素数量稳定）
- 加载状态检测
- 转换为 ElementFingerprint 对象
"""

from typing import List, Optional, Dict, Any, TYPE_CHECKING
import time

if TYPE_CHECKING:
    from ..fingerprint import ElementFingerprint


class PageScanner:
    """
    页面元素扫描器
    
    使用 JavaScript 注入方式扫描页面中的所有可交互元素，
    并转换为 ElementFingerprint 对象列表。
    """
    
    # 稳定性检测参数
    MAX_POLLS = 5              # 最大轮询次数
    POLL_INTERVAL = 0.5        # 轮询间隔（秒）
    STABLE_THRESHOLD = 3       # 连续稳定次数阈值
    
    @staticmethod
    def get_analysis_js() -> str:
        """
        获取页面分析 JavaScript 代码
        
        Returns:
            可执行的 JavaScript 代码字符串
        """
        from ...utils.js_store import PAGE_SCANNER_JS
        return PAGE_SCANNER_JS
    
    @classmethod
    def scan_page(cls, tab, timeout: float = 10.0) -> List[Dict[str, Any]]:
        """
        扫描页面元素（原始数据）
        
        Args:
            tab: DrissionPage 的 tab 对象
            timeout: 超时时间（秒）
            
        Returns:
            元素原始数据列表
        """
        print("=== 🚀 启动 JS 快照扫描（v3.0 稳定性增强模式） ===")
        print("🔄 正在执行 JS 批量扫描...")
        
        best_result = []
        stable_count = 0
        last_count = -1
        start_time = time.time()
        
        for poll in range(cls.MAX_POLLS):
            if time.time() - start_time > timeout:
                print(f"⚠️ 扫描超时 ({timeout}s)，使用当前结果")
                break
                
            try:
                js_result = tab.run_js(cls.get_analysis_js())
                
                # 处理加载状态
                if isinstance(js_result, dict):
                    if js_result.get('status') == 'loading':
                        loader = js_result.get('loader', 'unknown')
                        print(f"   ⏳ 页面加载中 ({loader})... 等待")
                        time.sleep(cls.POLL_INTERVAL)
                        continue
                    elif js_result.get('error'):
                        print(f"   ❌ JS 执行错误: {js_result.get('error')}")
                        break
                
                # 有效结果
                if isinstance(js_result, list):
                    current_count = len(js_result)
                    
                    if current_count == last_count and current_count > 0:
                        stable_count += 1
                        if stable_count >= cls.STABLE_THRESHOLD:
                            print(f"✅ 页面稳定 (连续 {cls.STABLE_THRESHOLD} 次检测到 {current_count} 个元素)")
                            best_result = js_result
                            break
                    else:
                        stable_count = 0
                        if current_count > len(best_result):
                            best_result = js_result
                    
                    last_count = current_count
                    
            except Exception as e:
                print(f"   ⚠️ 扫描异常: {e}")
                
            time.sleep(cls.POLL_INTERVAL)
        
        print(f"📊 JS 扫描完成，发现 {len(best_result)} 个可交互元素")
        return best_result
    
    @classmethod
    def scan_to_fingerprints(cls, tab, timeout: float = 10.0) -> List['ElementFingerprint']:
        """
        扫描页面并转换为 ElementFingerprint 列表
        
        Args:
            tab: DrissionPage 的 tab 对象
            timeout: 超时时间
            
        Returns:
            ElementFingerprint 对象列表
        """
        from ..fingerprint import ElementFingerprint
        
        raw_elements = cls.scan_page(tab, timeout)
        fingerprints = []
        
        for item in raw_elements:
            try:
                fp = ElementFingerprint(item)
                fingerprints.append(fp)
            except Exception:
                continue
        
        # 统计信息
        table_count = sum(1 for fp in fingerprints if fp.raw_data.get('is_table_cell'))
        visual_count = sum(1 for fp in fingerprints if fp.raw_data.get('visual_label'))
        shadow_count = sum(1 for fp in fingerprints if fp.raw_data.get('shadow_depth', 0) > 0)
        
        print(f"✅ 主文档扫描完成！发现 {len(fingerprints)} 个多维指纹")
        print(f"   表格元素: {table_count} 个")
        print(f"   视觉匹配: {visual_count} 个")
        print(f"   Shadow DOM: {shadow_count} 个")
        
        return fingerprints
