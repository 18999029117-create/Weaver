"""
Excel 适配器 - 基础设施层

封装 Excel/Pandas 数据操作，从 UI 层抽离。
"""
from typing import Optional, Any, Dict, List
import pandas as pd


class ExcelAdapter:
    """Excel 数据适配器"""
    
    def __init__(self, data: pd.DataFrame):
        self._data = data
    
    @property
    def data(self) -> pd.DataFrame:
        return self._data
    
    @property
    def columns(self) -> List[str]:
        return self._data.columns.tolist()
    
    @property
    def row_count(self) -> int:
        return len(self._data)
    
    def get_row(self, index: int) -> pd.Series:
        """获取指定行数据"""
        return self._data.iloc[index]
    
    def get_cell(self, row: int, column: str) -> Any:
        """获取单元格值"""
        return self._data.iloc[row].get(column)
    
    def add_computed_column(self, name: str, group_by: str, target: str, operation: str) -> bool:
        """
        添加计算列
        
        Args:
            name: 新列名
            group_by: 分组依据列
            target: 计算目标列
            operation: 操作类型 (count, sum, mean, max, min)
        """
        try:
            if operation == 'count':
                self._data[name] = self._data.groupby(group_by)[group_by].transform('count')
            else:
                temp_df = self._data.copy()
                temp_df[target] = pd.to_numeric(temp_df[target], errors='coerce')
                self._data[name] = temp_df.groupby(group_by)[target].transform(operation)
            return True
        except Exception as e:
            print(f"ExcelAdapter.add_computed_column error: {e}")
            return False
    
    def filter_by_anchor(self, column: str, values: List[str]) -> pd.DataFrame:
        """按锚点值过滤数据"""
        return self._data[self._data[column].astype(str).str.strip().isin(values)]
    
    def iterate_rows(self):
        """迭代所有行"""
        for idx, row in self._data.iterrows():
            yield idx, row
