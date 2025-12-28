"""
元素选择器加载器

从 element_selectors.json 加载元素定位配置，
提供多策略元素定位能力。
"""

import json
import os
from typing import Any, Dict, List, Optional, Tuple


class ElementLoader:
    """
    元素选择器加载器
    
    从 JSON 配置文件加载元素选择器，支持多策略定位。
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化加载器
        
        Args:
            config_path: JSON 配置文件路径，默认为项目根目录的 element_selectors.json
        """
        if config_path is None:
            # 默认路径：项目根目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            config_path = os.path.join(project_root, 'element_selectors.json')
        
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """加载 JSON 配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            print(f"[ElementLoader] ✅ 已加载配置: {self.config_path}")
        except FileNotFoundError:
            print(f"[ElementLoader] ⚠️ 配置文件不存在: {self.config_path}")
            self.config = {}
        except json.JSONDecodeError as e:
            print(f"[ElementLoader] ❌ 配置文件格式错误: {e}")
            self.config = {}
    
    def get_selectors(self, category: str, name: str) -> List[Dict[str, Any]]:
        """
        获取指定元素的选择器列表
        
        Args:
            category: 元素类别（如 "按钮"、"输入框"）
            name: 元素名称（如 "添加产品"、"医用耗材代码"）
            
        Returns:
            选择器列表，按优先级排序
        """
        try:
            element_config = self.config.get(category, {}).get(name, {})
            selectors = element_config.get('定位策略', [])
            # 按优先级排序
            return sorted(selectors, key=lambda x: x.get('优先级', 999))
        except Exception as e:
            print(f"[ElementLoader] 获取选择器失败: {e}")
            return []
    
    def get_button_selectors(self, name: str) -> List[Dict[str, Any]]:
        """获取按钮选择器"""
        return self.get_selectors('按钮', name)
    
    def get_input_selectors(self, name: str) -> List[Dict[str, Any]]:
        """获取输入框选择器"""
        return self.get_selectors('输入框', name)
    
    def get_table_selectors(self, name: str) -> List[Dict[str, Any]]:
        """获取表格操作选择器"""
        return self.get_selectors('表格操作', name)
    
    def try_locate(
        self, 
        tab: Any, 
        category: str, 
        name: str,
        timeout: float = 2.0,
        in_iframe: bool = False
    ) -> Tuple[Optional[Any], str]:
        """
        使用多种选择器依次尝试定位元素
        
        Args:
            tab: DrissionPage 的 tab/frame 对象
            category: 元素类别
            name: 元素名称
            timeout: 超时时间（秒）
            in_iframe: 是否在 iframe 内查找
            
        Returns:
            (元素对象, 成功使用的选择器) 或 (None, '')
        """
        selectors = self.get_selectors(category, name)
        
        if not selectors:
            print(f"[ElementLoader] ⚠️ 未找到 {category}/{name} 的选择器配置")
            return None, ''
        
        target = tab
        
        # 如果需要在 iframe 内查找，先尝试切换
        if in_iframe:
            try:
                # 尝试获取第一个 iframe
                iframe = tab.ele('tag:iframe', timeout=1)
                if iframe:
                    target = iframe
                    print(f"[ElementLoader] 已切换到 iframe")
            except:
                pass
        
        # 依次尝试每个选择器
        for selector_config in selectors:
            method = selector_config.get('方式', 'xpath')
            value = selector_config.get('值', '')
            
            if not value:
                continue
            
            try:
                # 根据定位方式构建选择器字符串
                if method == 'xpath':
                    selector = f'xpath:{value}'
                elif method == 'css':
                    selector = f'css:{value}'
                else:
                    selector = value
                
                elem = target.ele(selector, timeout=timeout)
                if elem:
                    print(f"[ElementLoader] ✅ 定位成功: {name} (使用: {method})")
                    return elem, selector
                    
            except Exception as e:
                # 继续尝试下一个选择器
                continue
        
        print(f"[ElementLoader] ❌ 无法定位: {name}")
        return None, ''
    
    def try_locate_button(self, tab: Any, name: str, **kwargs) -> Tuple[Optional[Any], str]:
        """定位按钮"""
        return self.try_locate(tab, '按钮', name, **kwargs)
    
    def try_locate_input(self, tab: Any, name: str, **kwargs) -> Tuple[Optional[Any], str]:
        """定位输入框"""
        return self.try_locate(tab, '输入框', name, **kwargs)
    
    def try_locate_table_element(self, tab: Any, name: str, **kwargs) -> Tuple[Optional[Any], str]:
        """定位表格元素"""
        return self.try_locate(tab, '表格操作', name, **kwargs)
    
    def wait_for_loading(self, tab: Any, timeout: float = 5.0) -> bool:
        """
        等待页面加载完成（loading 遮罩消失）
        
        Args:
            tab: DrissionPage 的 tab 对象
            timeout: 最大等待时间
            
        Returns:
            是否加载完成
        """
        import time
        start = time.time()
        
        while time.time() - start < timeout:
            try:
                # 检查是否存在 loading 遮罩
                loading = tab.ele('css:.el-loading-mask', timeout=0.2)
                if not loading:
                    return True
                
                # 检查遮罩是否隐藏
                style = loading.attr('style') or ''
                if 'display: none' in style or 'display:none' in style:
                    return True
                    
            except:
                return True
            
            time.sleep(0.3)
        
        return False
