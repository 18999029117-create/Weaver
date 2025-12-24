"""
锚定配置数据结构

定义多重锚定匹配所需的数据类型。
遵循 CONTRIBUTING.md 中的类型注解和文档规范。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class AnchorPair:
    """
    单个锚定列配对
    
    表示 Excel 中的一列与网页中对应列的映射关系。
    用于在填入数据前精确匹配行。
    
    Attributes:
        excel_column: Excel 中的列名
        web_column_xpath: 网页列的 XPath 选择器
        web_column_label: 网页列的显示名称（表头文本）
        enabled: 是否启用此锚定对
    """
    excel_column: str
    web_column_xpath: str
    web_column_label: str
    enabled: bool = True
    
    def __str__(self) -> str:
        status = "✓" if self.enabled else "✗"
        return f"[{status}] Excel[{self.excel_column}] ↔ Web[{self.web_column_label}]"


@dataclass
class WebColumnInfo:
    """
    网页列信息
    
    扫描网页表格时提取的列信息。
    
    Attributes:
        label: 列标题文本
        xpath: 列的 XPath 选择器
        is_readonly: 是否为只读列（用于锚定）
        is_input: 是否为输入框列（用于填入）
        sample_values: 示例值列表（用于匹配验证）
    """
    label: str
    xpath: str
    is_readonly: bool = True
    is_input: bool = False
    sample_values: List[str] = field(default_factory=list)
    
    def __str__(self) -> str:
        type_str = "只读" if self.is_readonly else "输入"
        return f"{self.label} ({type_str})"


@dataclass
class AnchorConfig:
    """
    锚定配置
    
    包含完整的锚定匹配配置，包括锚定列配对和待填列映射。
    
    Attributes:
        anchor_pairs: 锚定列配对列表（用于行匹配）
        fill_mappings: 待填入列映射 {excel_col: fingerprint}
        auto_matched: 是否为自动匹配生成的配置
        match_confidence: 自动匹配置信度（0-100）
    """
    anchor_pairs: List[AnchorPair] = field(default_factory=list)
    fill_mappings: Dict[str, Any] = field(default_factory=dict)
    auto_matched: bool = False
    match_confidence: float = 0.0
    
    @property
    def enabled_anchors(self) -> List[AnchorPair]:
        """获取已启用的锚定列配对"""
        return [p for p in self.anchor_pairs if p.enabled]
    
    @property
    def anchor_count(self) -> int:
        """获取已启用的锚定列数量"""
        return len(self.enabled_anchors)
    
    def get_excel_anchor_columns(self) -> List[str]:
        """获取所有已启用锚定列的 Excel 列名"""
        return [p.excel_column for p in self.enabled_anchors]
    
    def get_web_anchor_xpaths(self) -> List[str]:
        """获取所有已启用锚定列的网页 XPath"""
        return [p.web_column_xpath for p in self.enabled_anchors]
    
    def add_anchor_pair(self, excel_col: str, web_xpath: str, web_label: str) -> None:
        """添加一个锚定列配对"""
        self.anchor_pairs.append(AnchorPair(
            excel_column=excel_col,
            web_column_xpath=web_xpath,
            web_column_label=web_label,
            enabled=True
        ))
    
    def remove_anchor_pair(self, index: int) -> None:
        """移除指定索引的锚定列配对"""
        if 0 <= index < len(self.anchor_pairs):
            self.anchor_pairs.pop(index)
    
    def toggle_anchor_pair(self, index: int) -> None:
        """切换指定索引的锚定列配对启用状态"""
        if 0 <= index < len(self.anchor_pairs):
            self.anchor_pairs[index].enabled = not self.anchor_pairs[index].enabled
    
    def is_valid(self) -> bool:
        """检查配置是否有效（至少有一个启用的锚定列）"""
        return self.anchor_count > 0
    
    def __str__(self) -> str:
        mode = "自动" if self.auto_matched else "手动"
        return f"AnchorConfig({mode}, {self.anchor_count}个锚定列, 置信度:{self.match_confidence:.0f}%)"
