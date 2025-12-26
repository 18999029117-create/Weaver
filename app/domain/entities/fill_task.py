"""
填充任务数据类

定义单个填充任务的数据结构，将锚点解析结果与填充执行解耦。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class FillTask:
    """
    单个填充任务
    
    表示"将 Excel 第 N 行数据填入网页第 M 行输入框"的任务。
    锚点解析器负责生成这些任务，填充执行器只需按队列顺序执行。
    
    Attributes:
        excel_row_idx: Excel 数据行索引 (0-indexed)
        web_row_idx: 网页输入框行索引 (0-indexed，锚点解析后确定)
        row_data: 该行的数据 {列名: 值}
        anchor_value: 锚点列的值（用于调试/日志）
        status: 任务状态 - pending/success/error/skipped
        error_message: 错误信息（仅 status=error 时有值）
    """
    excel_row_idx: int
    web_row_idx: int
    row_data: Dict[str, Any]
    anchor_value: Optional[str] = None
    status: str = "pending"
    error_message: Optional[str] = None
    
    def mark_success(self):
        """标记为成功"""
        self.status = "success"
    
    def mark_error(self, message: str):
        """标记为失败"""
        self.status = "error"
        self.error_message = message
    
    def mark_skipped(self, reason: str = ""):
        """标记为跳过"""
        self.status = "skipped"
        self.error_message = reason
    
    @property
    def is_pending(self) -> bool:
        return self.status == "pending"
    
    @property
    def display_row(self) -> int:
        """显示用的行号 (1-indexed)"""
        return self.excel_row_idx + 1
