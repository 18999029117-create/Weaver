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
