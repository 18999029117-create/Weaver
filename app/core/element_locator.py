# -*- coding: utf-8 -*-
"""
多策略元素定位器 - 确保每次都能准确找到元素

使用方法:
    locator = ElementLocator(page)
    element = locator.找元素("添加产品")  # 通过名称找按钮
    locator.点击按钮("查询")
    locator.输入文本("医用耗材代码", "HIS-001")

新功能 - 本地缓存:
    - 成功找到元素后，自动缓存有效的选择器
    - 下次直接使用缓存的选择器，极大提升速度
    - 缓存保存到本地文件，软件重启后仍有效
    - 如果缓存失效（网页变化），自动重新查找并更新缓存
"""

import json
import os
import time
from typing import Optional, Any, Dict
from pathlib import Path
from datetime import datetime


# 缓存文件路径（保存在项目根目录）
_CACHE_FILE = Path(__file__).parent.parent.parent / "element_selector_cache.json"


class ElementLocator:
    """多策略元素定位器，自动尝试多种方式直到成功"""
    
    def __init__(self, page, config_path: str = None):
        """
        初始化定位器
        
        Args:
            page: DrissionPage 的页面对象 (ChromiumPage 或 WebPage)
            config_path: 选择器配置文件路径，默认使用 element_selectors.json
        """
        self.page = page
        self.config = self._加载配置(config_path)
        self.超时时间 = self.config.get("元素定位配置", {}).get("超时设置", 10)
        self.重试次数 = self.config.get("元素定位配置", {}).get("重试次数", 3)
        
        # 加载本地缓存
        self._选择器缓存 = self._加载缓存()
    
    def _加载缓存(self) -> Dict[str, dict]:
        """从本地文件加载选择器缓存"""
        if _CACHE_FILE.exists():
            try:
                with open(_CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    print(f"📂 已加载元素缓存 ({len(cache)} 个元素)")
                    return cache
            except Exception as e:
                print(f"⚠️ 缓存文件读取失败: {e}")
        return {}
    
    def _保存缓存(self):
        """将缓存保存到本地文件"""
        try:
            with open(_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._选择器缓存, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 缓存保存失败: {e}")
    
    def _加载配置(self, config_path: str = None) -> dict:
        """加载元素选择器配置文件"""
        if config_path is None:
            # 默认在项目根目录找配置文件
            root = Path(__file__).parent.parent.parent
            config_path = root / "element_selectors.json"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ 配置文件未找到: {config_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"⚠️ 配置文件格式错误: {e}")
            return {}
    
    def _获取元素配置(self, 元素名称: str) -> Optional[dict]:
        """根据名称查找元素配置"""
        # 在各个类别中查找
        for 类别 in ["输入框", "下拉框", "按钮", "Tab标签", "表格操作", "分页器", "对话框"]:
            if 类别 in self.config:
                元素集 = self.config[类别]
                if 元素名称 in 元素集:
                    return 元素集[元素名称]
        return None
    
    def 找元素(self, 元素名称: str, 超时: float = None):
        """
        通过元素名称查找元素，自动尝试多种定位策略
        
        新增缓存机制:
        1. 优先使用缓存的选择器（速度极快）
        2. 缓存失效时自动重新查找
        3. 成功后记录选择器和元素特征到本地文件
        
        Args:
            元素名称: 在配置文件中定义的元素名称，如 "添加产品"、"查询"
            超时: 等待超时时间（秒），默认使用配置中的值
        
        Returns:
            找到的元素对象，失败返回 None
        """
        timeout = 超时 or self.超时时间
        
        # ========== 1. 优先尝试缓存 ==========
        if 元素名称 in self._选择器缓存:
            缓存记录 = self._选择器缓存[元素名称]
            方式 = 缓存记录.get("方式", "xpath")
            值 = 缓存记录.get("值", "")
            
            start = time.time()
            元素 = self._用选择器查找(方式, 值, timeout=2)  # 缓存查找用短超时
            if 元素:
                耗时 = (time.time() - start) * 1000
                print(f"⚡ 快速找到 [{元素名称}] (缓存命中, {耗时:.0f}ms)")
                return 元素
            else:
                print(f"⚠️ 缓存失效 [{元素名称}], 重新查找...")
                del self._选择器缓存[元素名称]
        
        # ========== 2. 正常查找流程 ==========
        配置 = self._获取元素配置(元素名称)
        if not 配置:
            print(f"❌ 未找到元素配置: {元素名称}")
            return None
        
        定位策略列表 = 配置.get("定位策略", [])
        
        for 策略 in sorted(定位策略列表, key=lambda x: x.get("优先级", 99)):
            方式 = 策略.get("方式", "xpath")
            值 = 策略.get("值", "")
            说明 = 策略.get("说明", "")
            
            元素 = self._用选择器查找(方式, 值, timeout)
            if 元素:
                print(f"✅ 找到元素 [{元素名称}] - 使用策略: {说明 or 方式}")
                
                # ========== 3. 采集特征并缓存 ==========
                self._缓存选择器(元素名称, 方式, 值, 元素)
                return 元素
        
        print(f"❌ 所有策略都未能找到元素: {元素名称}")
        return None
    
    def _用选择器查找(self, 方式: str, 值: str, timeout: float):
        """使用单个选择器查找元素"""
        try:
            if 方式 == "xpath":
                return self.page.ele(f'xpath:{值}', timeout=timeout)
            elif 方式 == "css":
                return self.page.ele(f'css:{值}', timeout=timeout)
            else:
                return self.page.ele(值, timeout=timeout)
        except:
            return None
    
    def _缓存选择器(self, 元素名称: str, 方式: str, 值: str, 元素):
        """缓存成功的选择器，同时记录元素特征供分析"""
        try:
            # 采集元素特征
            特征 = {
                "id": 元素.attr("id") or "",
                "class": 元素.attr("class") or "",
                "text": (元素.text or "")[:50],  # 截取前50字符
                "tag": 元素.tag,
                "name": 元素.attr("name") or "",
                "placeholder": 元素.attr("placeholder") or "",
            }
        except:
            特征 = {}
        
        # 保存到缓存
        self._选择器缓存[元素名称] = {
            "方式": 方式,
            "值": 值,
            "特征": 特征,
            "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "命中次数": self._选择器缓存.get(元素名称, {}).get("命中次数", 0) + 1
        }
        self._保存缓存()
        print(f"💾 已缓存选择器 [{元素名称}]")
    
    def 点击按钮(self, 按钮名称: str, 等待加载: bool = True) -> bool:
        """
        点击指定名称的按钮
        
        Args:
            按钮名称: 按钮名称，如 "查询"、"添加产品"
            等待加载: 点击后是否等待页面加载
        
        Returns:
            是否成功
        """
        元素 = self.找元素(按钮名称)
        if 元素:
            try:
                元素.click()
                print(f"🖱️ 已点击按钮: {按钮名称}")
                if 等待加载:
                    self._等待加载完成()
                return True
            except Exception as e:
                print(f"❌ 点击失败: {按钮名称} - {e}")
        return False
    
    def 输入文本(self, 输入框名称: str, 文本: str, 清空原有: bool = True) -> bool:
        """
        在指定输入框中输入文本
        
        Args:
            输入框名称: 输入框名称，如 "医用耗材代码"
            文本: 要输入的文本
            清空原有: 是否先清空原有内容
        
        Returns:
            是否成功
        """
        元素 = self.找元素(输入框名称)
        if 元素:
            try:
                if 清空原有:
                    元素.clear()
                元素.input(文本)
                print(f"⌨️ 已输入 [{输入框名称}]: {文本}")
                return True
            except Exception as e:
                print(f"❌ 输入失败: {输入框名称} - {e}")
        return False
    
    def 选择下拉项(self, 下拉框名称: str, 选项文本: str) -> bool:
        """
        选择下拉框中的选项
        
        Args:
            下拉框名称: 下拉框名称
            选项文本: 要选择的选项文字
        
        Returns:
            是否成功
        """
        # 先点击下拉框打开选项列表
        下拉框 = self.找元素(下拉框名称)
        if not 下拉框:
            return False
        
        try:
            下拉框.click()
            self.page.wait(0.5)  # 等待下拉动画
            
            # 查找并点击选项
            选项 = self.page.ele(f'xpath://li[contains(@class,"el-select-dropdown__item")][contains(.,"{选项文本}")]')
            if 选项:
                选项.click()
                print(f"📋 已选择 [{下拉框名称}]: {选项文本}")
                return True
            else:
                print(f"❌ 未找到选项: {选项文本}")
                
        except Exception as e:
            print(f"❌ 选择失败: {下拉框名称} - {e}")
        
        return False
    
    def 点击Tab(self, Tab名称: str) -> bool:
        """切换到指定Tab标签页"""
        return self.点击按钮(Tab名称, 等待加载=True)
    
    def 获取表格行数(self) -> int:
        """获取表格当前数据行数"""
        try:
            行元素列表 = self.page.eles('xpath://tbody//tr[contains(@class,"el-table__row")]')
            return len(行元素列表)
        except:
            return 0
    
    def 填写表格单元格(self, 行号: int, 列名: str, 值: str) -> bool:
        """
        填写表格中指定单元格
        
        Args:
            行号: 行号（从1开始）
            列名: 列名，如 "采购数量"、"备注"
            值: 要填写的值
        """
        配置 = self._获取元素配置(f"{列名}输入框")
        if not 配置:
            print(f"❌ 未找到列配置: {列名}")
            return False
        
        模板 = 配置.get("行定位模板", "")
        if not 模板:
            print(f"❌ 列 {列名} 未配置行定位模板")
            return False
        
        xpath = 模板.replace("{row_index}", str(行号))
        try:
            输入框 = self.page.ele(f'xpath:{xpath}')
            if 输入框:
                输入框.clear()
                输入框.input(值)
                print(f"📝 表格[行{行号}][{列名}] = {值}")
                return True
        except Exception as e:
            print(f"❌ 表格填写失败: 行{行号} {列名} - {e}")
        
        return False
    
    def _等待加载完成(self, 超时: float = 10):
        """等待页面加载完成（loading遮罩消失）"""
        try:
            # 等待 loading 遮罩消失
            self.page.wait.ele_hidden('css:.el-loading-mask', timeout=超时)
        except:
            pass  # 超时不报错，可能本来就没有loading
    
    def 检查元素是否存在(self, 元素名称: str) -> bool:
        """检查元素是否存在"""
        元素 = self.找元素(元素名称, 超时=2)
        return 元素 is not None
    
    def 获取元素文本(self, 元素名称: str) -> str:
        """获取元素的文本内容"""
        元素 = self.找元素(元素名称)
        if 元素:
            return 元素.text
        return ""


# 使用示例
if __name__ == "__main__":
    print("=" * 50)
    print("元素定位器使用示例")
    print("=" * 50)
    print("""
from DrissionPage import ChromiumPage
from app.core.element_locator import ElementLocator

# 初始化
page = ChromiumPage()
locator = ElementLocator(page)

# 点击按钮
locator.点击按钮("添加产品")
locator.点击按钮("查询")

# 输入文本
locator.输入文本("医用耗材代码", "HIS-001")

# 选择下拉框
locator.选择下拉项("挂网状态", "已挂网")

# 切换Tab
locator.点击Tab("待审核")

# 填写表格
locator.填写表格单元格(行号=1, 列名="采购数量", 值="100")
    """)
