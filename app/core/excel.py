"""
Excel 管理器

负责 Excel 文件的加载、预览和数据管理。
集成智能表头检测功能。
"""

import pandas as pd
import os
from typing import Tuple, List, Optional

from app.infrastructure.excel.header_detector import ExcelHeaderDetector


class ExcelManager:
    """
    Excel 数据管理器
    
    支持智能表头检测和手动指定表头行。
    """
    
    def __init__(self):
        self.data: Optional[pd.DataFrame] = None
        self.file_path: Optional[str] = None
        self.header_row: int = 0
        self.header_confidence: float = 0.0
    
    def load_excel(self, file_path: str, header_row: Optional[int] = None) -> pd.DataFrame:
        """
        读取 Excel 文件
        
        Args:
            file_path: 文件路径
            header_row: 表头行号 (0-based)，None 表示自动检测
            
        Returns:
            加载后的 DataFrame
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件未找到: {file_path}")
        
        self.file_path = file_path
        
        if header_row is None:
            # 自动检测表头行
            detected_row, confidence = ExcelHeaderDetector.detect(file_path)
            self.header_row = detected_row
            self.header_confidence = confidence
        else:
            self.header_row = header_row
            self.header_confidence = 100.0  # 用户手动指定，100% 置信
        
        # 读取数据
        self.data = pd.read_excel(
            file_path, 
            header=self.header_row
        ).fillna("")
        
        print(f"[ExcelManager] 加载成功: {len(self.data)} 行, 表头第{self.header_row + 1}行")
        return self.data
    
    def detect_header(self, file_path: str) -> Tuple[int, float]:
        """
        检测文件的表头行
        
        Args:
            file_path: 文件路径
            
        Returns:
            (row_index, confidence): 表头行号和置信度
        """
        return ExcelHeaderDetector.detect(file_path)
    
    def get_raw_preview(self, file_path: str, rows: int = 10) -> pd.DataFrame:
        """
        获取原始预览数据（不指定表头）
        
        用于表头选择对话框显示。
        
        Args:
            file_path: 文件路径
            rows: 预览行数
            
        Returns:
            原始 DataFrame
        """
        return ExcelHeaderDetector.get_raw_preview(file_path, rows)
    
    def get_preview_data(self, rows: int = 50) -> Tuple[List[str], List[list]]:
        """
        获取已加载数据的预览
        
        Args:
            rows: 预览行数
            
        Returns:
            (columns, data_rows): 列名列表和数据行列表
        """
        if self.data is None:
            return [], []
        
        columns = self.data.columns.tolist()
        data_rows = self.data.head(rows).values.tolist()
        return columns, data_rows
    
    def reload_with_header(self, header_row: int) -> pd.DataFrame:
        """
        使用新的表头行重新加载
        
        Args:
            header_row: 新的表头行号 (0-based)
            
        Returns:
            重新加载的 DataFrame
        """
        if not self.file_path:
            raise ValueError("没有已加载的文件")
        
        return self.load_excel(self.file_path, header_row)
    
    @property
    def needs_header_confirmation(self) -> bool:
        """
        是否需要用户确认表头
        
        置信度低于 70% 时需要确认
        """
        return self.header_confidence < 70

