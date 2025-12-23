"""
填充进度相关数据模型

包含:
- FillRecord: 单条填充记录
- FillProgress: 填充进度状态
- PageState: 页面状态快照
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any


@dataclass
class FillRecord:
    """单条填充记录"""
    excel_row: int              # Excel行号（1-indexed，与用户看到的一致）
    page_number: int            # 网页页码
    web_row: int                # 网页表格行号（当页内的行号）
    field_values: Dict[str, str]  # 填充的字段值 {字段名: 值}
    status: str                 # success / failed / skipped
    timestamp: str              # ISO格式时间戳
    error_msg: str = ""         # 错误信息
    anchor_value: str = ""      # 锚定列的值（用于对比验证）
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FillRecord':
        return cls(**data)


@dataclass
class FillProgress:
    """填充进度状态"""
    excel_file: str = ""              # Excel文件路径
    total_rows: int = 0               # 总行数
    current_excel_row: int = 1        # 当前Excel行号（下一个要填充的行）
    filled_count: int = 0             # 已成功填充数
    failed_count: int = 0             # 失败数
    current_page: int = 1             # 当前页码
    anchor_column: str = ""           # 锚定列名（用于数据对比）
    started_at: str = ""              # 开始时间
    updated_at: str = ""              # 最后更新时间
    status: str = "idle"              # idle / running / paused / completed / error
    records: List[FillRecord] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['records'] = [r.to_dict() if isinstance(r, FillRecord) else r for r in self.records]
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FillProgress':
        records = [FillRecord.from_dict(r) for r in data.pop('records', [])]
        progress = cls(**data)
        progress.records = records
        return progress


@dataclass
class PageState:
    """页面状态快照"""
    page_number: int = 1
    url: str = ""
    content_hash: str = ""
    element_count: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
