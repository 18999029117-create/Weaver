import pandas as pd
import os

class ExcelManager:
    def __init__(self):
        self.data = None
        self.file_path = None

    def load_excel(self, file_path):
        """读取 Excel 文件"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件未找到: {file_path}")
        
        # 读取所有列，并将空值处理为空字符串
        self.data = pd.read_excel(file_path).fillna("")
        self.file_path = file_path
        return self.data

    def get_preview_data(self, rows=50):
        """获取前 N 行用于预览"""
        if self.data is None:
            return [], []
        
        columns = self.data.columns.tolist()
        data_rows = self.data.head(rows).values.tolist()
        return columns, data_rows
