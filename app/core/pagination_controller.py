"""
翻页控制器 - 管理分页填充的翻页逻辑
支持用户指定翻页按钮、页面变化检测、自动翻页执行
"""
import time
from dataclasses import dataclass, field
from typing import Optional, Callable
from datetime import datetime


@dataclass
class PageState:
    """页面状态快照"""
    page_number: int = 1
    url: str = ""
    content_hash: str = ""
    element_count: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


class PaginationController:
    """
    翻页控制器
    
    功能:
    - 用户指定翻页按钮选择器
    - 检测页面是否发生变化
    - 执行翻页操作
    - 等待新页面加载完成
    """
    
    def __init__(self, tab):
        """
        初始化翻页控制器
        
        Args:
            tab: DrissionPage 的 tab 对象
        """
        self.tab = tab
        self.next_button_selector: Optional[str] = None
        self.next_button_xpath: Optional[str] = None
        self.current_page: int = 1
        self.last_page_state: Optional[PageState] = None
        self.page_change_callbacks: list[Callable] = []
        
    def set_next_button(self, selector: str = None, xpath: str = None):
        """
        设置翻页按钮
        
        Args:
            selector: CSS选择器
            xpath: XPath选择器
        """
        self.next_button_selector = selector
        self.next_button_xpath = xpath
        print(f"✅ 翻页按钮已设置: {selector or xpath}")
        
    def capture_page_state(self) -> PageState:
        """
        捕获当前页面状态
        
        Returns:
            PageState: 页面状态快照
        """
        try:
            # 获取页面URL
            url = self.tab.url or ""
            
            # 使用DrissionPage原生方法获取页面特征
            content_hash = ""
            
            # 方法1: 获取分页指示器
            selectors = [
                '#current-page-display',
                '.current-page-display', 
                '.page-num.current',
                '.pagination .active',
                '.ant-pagination-item-active',
                '.el-pager .active'
            ]
            for sel in selectors:
                el = self.tab.ele(sel, timeout=0.5)
                if el:
                    content_hash = f"page:{el.text}"
                    break
            
            # 方法2: 获取表格首行序号
            if not content_hash:
                row_selectors = ['.row-num', 'table tbody tr td:first-child']
                for sel in row_selectors:
                    el = self.tab.ele(sel, timeout=0.5)
                    if el:
                        content_hash = f"row:{el.text}"
                        break
            
            # 方法3: 获取第一个输入框的值
            if not content_hash:
                el = self.tab.ele('table tbody input', timeout=0.5)
                if el:
                    content_hash = f"input:{el.value or el.attr('placeholder') or ''}"
            
            # 方法4: 使用时间戳（备用）
            if not content_hash:
                content_hash = f"time:{self.tab.url}:{time.time()}"
            
            # 获取可交互元素数量
            element_count = len(self.tab.eles('input, select, textarea')) if hasattr(self.tab, 'eles') else 0
            
            return PageState(
                page_number=self.current_page,
                url=url,
                content_hash=content_hash,
                element_count=element_count,
                timestamp=datetime.now()
            )
        except Exception as e:
            print(f"⚠️ 捕获页面状态失败: {e}")
            return PageState(page_number=self.current_page)
    
    def detect_page_change(self, old_state: PageState, new_state: PageState) -> bool:
        """
        检测页面是否发生变化
        
        Args:
            old_state: 旧状态
            new_state: 新状态
            
        Returns:
            bool: 是否发生变化
        """
        # URL变化
        if old_state.url != new_state.url:
            return True
        
        # 内容哈希变化
        if old_state.content_hash != new_state.content_hash:
            return True
        
        return False
    
    def click_next_page(self, wait_after: float = 1.0, max_retries: int = 3) -> bool:
        """
        点击翻页按钮（增强版：禁用检测 + 重试机制）
        
        Args:
            wait_after: 点击后等待时间（秒）
            max_retries: 最大重试次数
            
        Returns:
            bool: 是否成功翻页
        """
        if not self.next_button_selector and not self.next_button_xpath:
            print("❌ 未设置翻页按钮")
            return False
        
        for retry in range(max_retries):
            try:
                # 捕获点击前状态
                old_state = self.capture_page_state()
                
                # 尝试查找翻页按钮
                button = None
                if self.next_button_selector:
                    button = self.tab.ele(self.next_button_selector, timeout=3)
                if not button and self.next_button_xpath:
                    button = self.tab.ele(f'xpath:{self.next_button_xpath}', timeout=3)
                
                if not button:
                    print("❌ 未找到翻页按钮")
                    return False
                
                # === 增强：检查按钮是否被禁用 ===
                is_disabled = self._check_button_disabled(button)
                if is_disabled:
                    print("🛑 翻页按钮已禁用，已到达最后一页")
                    return False
                
                # 点击按钮
                button.click()
                print(f"🔄 点击翻页按钮，等待页面加载... (尝试 {retry + 1}/{max_retries})")
                
                # 等待页面变化
                time.sleep(wait_after)
                
                # 检测页面是否变化
                max_wait = 5  # 最大等待5秒
                start_time = time.time()
                
                while time.time() - start_time < max_wait:
                    new_state = self.capture_page_state()
                    if self.detect_page_change(old_state, new_state):
                        self.current_page += 1
                        self.last_page_state = new_state
                        print(f"✅ 翻页成功，当前第 {self.current_page} 页")
                        
                        # 触发回调
                        for callback in self.page_change_callbacks:
                            try:
                                callback(self.current_page, new_state)
                            except Exception as e:
                                print(f"⚠️ 页面变化回调执行失败: {e}")
                        
                        return True
                    
                    time.sleep(0.3)
                
                # 页面未变化，准备重试
                if retry < max_retries - 1:
                    print(f"⏳ 页面未变化，等待重试... ({retry + 1}/{max_retries})")
                    time.sleep(0.5)  # 短间隔后重试
                    continue
                    
            except Exception as e:
                print(f"❌ 翻页尝试 {retry + 1} 失败: {e}")
                if retry < max_retries - 1:
                    time.sleep(0.5)
                    continue
                return False
        
        # 所有重试都失败
        print("⚠️ 多次尝试后页面仍未变化，确认已是最后一页")
        return False
    
    def _check_button_disabled(self, button) -> bool:
        """
        检查按钮是否被禁用
        
        检测方式：
        1. disabled 属性
        2. aria-disabled="true"
        3. 特定禁用类名 (ant-pagination-disabled, disabled, el-button--disabled 等)
        
        Returns:
            bool: 是否禁用
        """
        try:
            # 方法1: 检查 disabled 属性
            disabled_attr = button.attr('disabled')
            if disabled_attr is not None and disabled_attr != 'false':
                return True
            
            # 方法2: 检查 aria-disabled
            aria_disabled = button.attr('aria-disabled')
            if aria_disabled == 'true':
                return True
            
            # 方法3: 检查类名
            class_name = button.attr('class') or ''
            disabled_classes = [
                'disabled', 'ant-pagination-disabled', 'el-button--disabled',
                'btn-disabled', 'is-disabled', 'pagination-disabled'
            ]
            for dc in disabled_classes:
                if dc in class_name.lower():
                    return True
            
            # 方法4: 使用 JS 进一步检测
            js_check = """
            (el) => {
                if (el.disabled) return true;
                if (el.getAttribute('aria-disabled') === 'true') return true;
                const style = window.getComputedStyle(el);
                if (style.pointerEvents === 'none') return true;
                if (style.opacity < 0.5) return true;
                return false;
            }
            """
            try:
                result = self.tab.run_js(js_check, button)
                if result:
                    return True
            except:
                pass
            
            return False
        except Exception as e:
            print(f"⚠️ 检查按钮状态失败: {e}")
            return False
    
    def wait_for_page_ready(self, timeout: float = 5.0) -> bool:
        """
        等待页面加载完成
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            bool: 是否加载完成
        """
        try:
            ready_js = """
            (() => {
                // 检查常见加载指示器
                const loaders = document.querySelectorAll(
                    '.loading, .spinner, .ant-spin-spinning, .el-loading-mask'
                );
                for (let loader of loaders) {
                    const style = window.getComputedStyle(loader);
                    if (style.display !== 'none' && style.visibility !== 'hidden') {
                        return false;
                    }
                }
                return document.readyState === 'complete';
            })();
            """
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self.tab.run_js(ready_js):
                    return True
                time.sleep(0.2)
            
            return False
            
        except Exception as e:
            print(f"⚠️ 检查页面就绪状态失败: {e}")
            return True  # 失败时假设已就绪
    
    def on_page_change(self, callback: Callable):
        """
        注册页面变化回调
        
        Args:
            callback: 回调函数 (page_number, page_state) -> None
        """
        self.page_change_callbacks.append(callback)
    
    def reset(self):
        """重置翻页状态"""
        self.current_page = 1
        self.last_page_state = None
        print("🔄 翻页状态已重置")
