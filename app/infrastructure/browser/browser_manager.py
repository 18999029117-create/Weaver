"""
浏览器管理器 - 基础设施层实现

封装 DrissionPage 的浏览器连接和标签页管理。
"""

from typing import List, Dict, Any, Optional
from DrissionPage import ChromiumPage
from app.utils.port_check import PortChecker


class BrowserManager:
    """
    浏览器管理器
    
    职责:
    - 连接浏览器
    - 管理标签页
    - 提供浏览器操作接口
    """
    
    def __init__(self, addr: str = '127.0.0.1:9222'):
        """
        初始化浏览器管理器
        
        Args:
            addr: 浏览器调试地址
        """
        self.addr = addr
        self.page: Optional[ChromiumPage] = None
    
    def connect(self) -> ChromiumPage:
        """
        连接浏览器
        
        Returns:
            ChromiumPage 对象
            
        Raises:
            ConnectionError: 无法连接到浏览器
        """
        host, port = self.addr.split(':')
        if not PortChecker.is_port_open(int(port), host):
            raise ConnectionError(f"无法连接到 {self.addr}。请确保浏览器已启用调试模式。")
        
        self.page = ChromiumPage(addr_or_opts=self.addr)
        return self.page
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.page is not None
    
    def get_tabs(self) -> List[Dict[str, Any]]:
        """
        获取所有打开的标签页
        
        Returns:
            标签页信息列表
        """
        if not self.page:
            self.connect()
        
        tabs = []
        for tab_id in self.page.tab_ids:
            try:
                tab = self.page.get_tab(tab_id)
                title = tab.title or "无标题"
                tabs.append({
                    "id": tab_id,
                    "title": title,
                    "url": tab.url
                })
            except:
                continue
        return tabs
    
    def get_tab(self, tab_id: str) -> Optional[Any]:
        """
        获取指定标签页
        
        Args:
            tab_id: 标签页 ID
            
        Returns:
            标签页对象或 None
        """
        if not self.page:
            return None
        try:
            return self.page.get_tab(tab_id)
        except:
            return None
    
    def get_current_tab(self) -> Optional[Any]:
        """获取当前活动标签页"""
        if not self.page:
            return None
        return self.page
    
    def run_js(self, script: str, tab: Optional[Any] = None) -> Any:
        """
        在标签页中执行 JavaScript
        
        Args:
            script: JavaScript 代码
            tab: 目标标签页（可选，默认当前页）
            
        Returns:
            执行结果
        """
        target = tab or self.page
        if target:
            return target.run_js(script)
        return None
    # ============================================================
    # 交互式选择模式 API (性能优化版)
    # ============================================================
    
    # 缓存已注入脚本的 Frame URL，避免重复扫描
    _injected_frame_urls: set = set()
    
    def inject_interaction_script(self, tab: Optional[Any] = None) -> bool:
        """
        注入交互式选择脚本（递归所有 Frame，只执行一次）
        
        优化策略：
        - 记录已注入的 Frame，避免重复
        - 只在首次调用时进行递归
        """
        from app.infrastructure.js.script_store import ScriptStore
        
        script = ScriptStore.get_interaction_js()
        if not script:
            print("[BrowserManager] Failed to load interaction script")
            return False
            
        target = tab or self.page
        if not target:
            return False

        success_count = 0
        
        def _inject_single(frame_obj):
            """注入单个 Frame"""
            nonlocal success_count
            try:
                frame_obj.run_js(script)
                success_count += 1
            except:
                pass
        
        def _traverse_and_inject(frame_obj, depth=0):
            """递归注入所有 Frame (最大深度限制)"""
            if depth > 3:
                return
                
            # 注入当前 Frame
            _inject_single(frame_obj)
            
            # 递归子 Frame
            try:
                frames = frame_obj.eles('tag:iframe')
                for frame_ele in frames:
                    try:
                        child = frame_obj.get_frame(frame_ele)
                        if child:
                            _traverse_and_inject(child, depth + 1)
                    except:
                        pass
            except:
                pass
        
        _traverse_and_inject(target)
        
        if success_count > 0:
            print(f"[BrowserManager] Interaction script injected into {success_count} frame(s)")
            # 确保注入后 pick mode 是启用的
            self.set_pick_mode(True, tab)
            
        return success_count > 0
    
    def get_picked_element(self, tab: Optional[Any] = None) -> Optional[Dict[str, Any]]:
        """
        获取用户双击选择的元素信息
        
        注意：DrissionPage run_js 需要显式 return 语句才能获取返回值
        """
        target = tab or self.page
        if not target:
            return None
        
        # 检查状态的 JS (需要 return)
        status_js = """return (function() {
            return {
                injected: !!window.__weaver_interaction_injected,
                pickMode: window.weaver_pick_mode,
                hasPicked: !!window.weaver_picked_element
            };
        })();"""
        
        # 获取并清除选中元素的 JS (需要 return)
        pick_js = """return (function() {
            if (window.weaver_get_and_clear_picked) {
                return window.weaver_get_and_clear_picked();
            }
            return null;
        })();"""
        
        # 1. 先查主文档
        try:
            result = target.run_js(pick_js)
            if result:
                print(f"[BrowserManager] 🎯 主文档捕获到元素!")
                return result
        except Exception as e:
            print(f"[BrowserManager] 主文档查询异常: {e}")
        
        # 2. 扫描 iframe
        try:
            frames = target.eles('tag:iframe')
            
            for i, frame_ele in enumerate(frames):
                try:
                    frame = target.get_frame(frame_ele)
                    if frame:
                        result = frame.run_js(pick_js)
                        if result:
                            result['frame_path'] = f"iframe[{i}]"
                            result['in_iframe'] = True
                            print(f"[BrowserManager] 🎯 iframe[{i}] 捕获到元素!")
                            return result
                except Exception as e:
                    print(f"[BrowserManager] iframe[{i}] 访问异常: {e}")
        except Exception as e:
            print(f"[BrowserManager] 获取 iframe 列表异常: {e}")
            
        return None
    
    def flash_elements(self, xpaths: List[str], tab: Optional[Any] = None) -> None:
        """
        让指定元素闪烁（广播到主文档和第一层 iframe）
        """
        if not xpaths:
            return
            
        target = tab or self.page
        if not target:
            return
        
        xpaths_json = str(xpaths).replace("'", '"')
        script = f"if (window.weaver_flash_elements) {{ window.weaver_flash_elements({xpaths_json}); }}"
        
        # 主文档
        try:
            target.run_js(script)
        except:
            pass
        
        # 第一层 iframe
        try:
            frames = target.eles('tag:iframe')
            for frame_ele in frames:
                try:
                    frame = target.get_frame(frame_ele)
                    if frame:
                        frame.run_js(script)
                except:
                    pass
        except:
            pass
    
    def set_pick_mode(self, enabled: bool, tab: Optional[Any] = None) -> None:
        """
        开启/关闭选择模式
        """
        target = tab or self.page
        if not target:
            return

        script = f"if (window.weaver_set_pick_mode) {{ window.weaver_set_pick_mode({str(enabled).lower()}); }}"
        
        try:
            target.run_js(script)
        except:
            pass
        
        # 第一层 iframe
        try:
            frames = target.eles('tag:iframe')
            for frame_ele in frames:
                try:
                    frame = target.get_frame(frame_ele)
                    if frame:
                        frame.run_js(script)
                except:
                    pass
        except:
            pass


