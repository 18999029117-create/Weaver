"""
填充进度管理器 - 追踪Excel行号、断点续传、填充日志
确保分页填充时数据的一致性和连贯性
"""
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path


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


class FillProgressManager:
    """
    填充进度管理器
    
    功能:
    - 追踪当前Excel行号（确保分页时连续）
    - 保存/加载进度（支持断点续传）
    - 记录每条填充日志
    - 锚定列对比验证
    """
    
    PROGRESS_DIR = Path.home() / ".weaver" / "progress"
    
    def __init__(self):
        self.progress: FillProgress = FillProgress()
        self.progress_file: Optional[Path] = None
        
        # 确保目录存在
        self.PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    
    def start_new_session(self, excel_file: str, total_rows: int, 
                          anchor_column: str = "", start_row: int = 1):
        """
        开始新的填充会话
        
        Args:
            excel_file: Excel文件路径
            total_rows: 总行数
            anchor_column: 锚定列名（可选）
            start_row: 起始行号（默认1）
        """
        self.progress = FillProgress(
            excel_file=excel_file,
            total_rows=total_rows,
            current_excel_row=start_row,
            filled_count=0,
            failed_count=0,
            current_page=1,
            anchor_column=anchor_column,
            started_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            status="running",
            records=[]
        )
        
        # 生成进度文件名
        filename = f"progress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.progress_file = self.PROGRESS_DIR / filename
        
        self._save_progress()
        print(f"📝 开始新会话: {total_rows}行数据，从第{start_row}行开始")
        if anchor_column:
            print(f"   锚定列: {anchor_column}")
    
    def get_next_excel_row(self) -> int:
        """
        获取下一个要填充的Excel行号
        
        Returns:
            int: Excel行号（1-indexed）
        """
        return self.progress.current_excel_row
    
    def get_remaining_count(self) -> int:
        """获取剩余未填充的行数"""
        return self.progress.total_rows - self.progress.current_excel_row + 1
    
    def has_more_data(self) -> bool:
        """是否还有数据需要填充"""
        return self.progress.current_excel_row <= self.progress.total_rows
    
    def add_fill_record(self, excel_row: int, web_row: int, 
                        field_values: Dict[str, str], status: str,
                        error_msg: str = "", anchor_value: str = ""):
        """
        添加填充记录
        
        Args:
            excel_row: Excel行号
            web_row: 网页表格行号（当页）
            field_values: 填充的字段值
            status: success/failed/skipped
            error_msg: 错误信息
            anchor_value: 锚定列值
        """
        record = FillRecord(
            excel_row=excel_row,
            page_number=self.progress.current_page,
            web_row=web_row,
            field_values=field_values,
            status=status,
            timestamp=datetime.now().isoformat(),
            error_msg=error_msg,
            anchor_value=anchor_value
        )
        
        self.progress.records.append(record)
        
        if status == "success":
            self.progress.filled_count += 1
            # 立即保存（容灾：每成功1条即保存）
            self._save_progress_async()
        elif status == "failed":
            self.progress.failed_count += 1
            # 失败也保存，记录错误状态
            self._save_progress_async()
        
        # 移动到下一行
        self.progress.current_excel_row = excel_row + 1
        self.progress.updated_at = datetime.now().isoformat()
    
    def on_page_turn(self, new_page: int):
        """
        翻页时更新状态
        
        Args:
            new_page: 新页码
        """
        self.progress.current_page = new_page
        self.progress.updated_at = datetime.now().isoformat()
        print(f"📄 翻到第 {new_page} 页，当前Excel行号: {self.progress.current_excel_row}")
        self._save_progress()
    
    def pause(self):
        """暂停填充"""
        self.progress.status = "paused"
        self.progress.updated_at = datetime.now().isoformat()
        self._save_progress()
        print(f"⏸️ 已暂停，进度: {self.progress.filled_count}/{self.progress.total_rows}")
    
    def resume(self):
        """恢复填充"""
        self.progress.status = "running"
        self.progress.updated_at = datetime.now().isoformat()
        print(f"▶️ 恢复填充，从第 {self.progress.current_excel_row} 行继续")
    
    def complete(self):
        """完成填充"""
        self.progress.status = "completed"
        self.progress.updated_at = datetime.now().isoformat()
        self._save_progress()
        print(f"✅ 填充完成! 成功: {self.progress.filled_count}, 失败: {self.progress.failed_count}")
    
    def _save_progress(self):
        """保存进度到文件（同步）"""
        if self.progress_file:
            try:
                with open(self.progress_file, 'w', encoding='utf-8') as f:
                    json.dump(self.progress.to_dict(), f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"⚠️ 保存进度失败: {e}")
    
    def _save_progress_async(self):
        """异步保存进度（不阻塞主线程）"""
        import threading
        
        def save_task():
            self._save_progress()
        
        # 使用守护线程异步保存
        t = threading.Thread(target=save_task, daemon=True)
        t.start()
    
    def load_progress(self, progress_file: str) -> bool:
        """
        加载进度文件
        
        Args:
            progress_file: 进度文件路径
            
        Returns:
            bool: 是否加载成功
        """
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.progress = FillProgress.from_dict(data)
            self.progress_file = Path(progress_file)
            
            print(f"📂 已加载进度文件")
            print(f"   Excel: {self.progress.excel_file}")
            print(f"   进度: {self.progress.filled_count}/{self.progress.total_rows}")
            print(f"   下一行: {self.progress.current_excel_row}")
            
            return True
        except Exception as e:
            print(f"❌ 加载进度失败: {e}")
            return False
    
    def get_summary(self) -> Dict[str, Any]:
        """获取进度摘要"""
        return {
            "total": self.progress.total_rows,
            "filled": self.progress.filled_count,
            "failed": self.progress.failed_count,
            "remaining": self.get_remaining_count(),
            "current_row": self.progress.current_excel_row,
            "current_page": self.progress.current_page,
            "status": self.progress.status,
            "progress_percent": round(self.progress.filled_count / max(self.progress.total_rows, 1) * 100, 1)
        }
    
    def get_fill_log(self, last_n: int = 20) -> List[FillRecord]:
        """
        获取最近的填充日志
        
        Args:
            last_n: 获取最近N条
            
        Returns:
            List[FillRecord]: 填充记录列表
        """
        return self.progress.records[-last_n:]
    
    def verify_anchor(self, excel_value: str, web_value: str) -> bool:
        """
        验证锚定列值是否匹配
        
        Args:
            excel_value: Excel中的锚定列值
            web_value: 网页中对应的值
            
        Returns:
            bool: 是否匹配
        """
        # 清理空白后比较
        excel_clean = str(excel_value).strip()
        web_clean = str(web_value).strip()
        
        if excel_clean == web_clean:
            return True
        
        # 尝试数值比较（处理格式差异如 "100" vs "100.0"）
        try:
            if float(excel_clean) == float(web_clean):
                return True
        except (ValueError, TypeError):
            pass
        
        return False
    
    def list_saved_progress(self) -> List[Dict]:
        """
        列出所有保存的进度文件
        
        Returns:
            List[Dict]: 进度文件列表
        """
        files = []
        for f in self.PROGRESS_DIR.glob("progress_*.json"):
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    data = json.load(fp)
                files.append({
                    "file": str(f),
                    "excel": data.get("excel_file", ""),
                    "progress": f"{data.get('filled_count', 0)}/{data.get('total_rows', 0)}",
                    "status": data.get("status", ""),
                    "updated": data.get("updated_at", "")
                })
            except:
                pass
        
        return sorted(files, key=lambda x: x.get("updated", ""), reverse=True)
