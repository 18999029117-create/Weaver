"""
Excel 表头智能检测器

通过多特征评分算法自动识别 Excel 文件的表头行。

特征评分:
- 列标题关键词 (+30)
- 数据类型一致性 (+25)
- 非空比例高 (+20)
- 非纯数字 (+15)
- 下方有足够数据行 (+10)
"""

from typing import Tuple, List, Optional
import pandas as pd
import re


class ExcelHeaderDetector:
    """
    Excel 表头智能检测器
    
    使用多特征评分算法识别最可能的表头行。
    """
    
    # 常见表头关键词 (中英文)
    HEADER_KEYWORDS = [
        # 中文
        '编号', '序号', '名称', '姓名', '日期', '时间', '数量', '单价', '金额',
        '电话', '地址', '邮箱', '备注', '状态', '类型', '规格', '单位', '厂家',
        '部门', '科室', '编码', '代码', '批次', '批号', '有效期', '生产日期',
        # 英文
        'id', 'name', 'date', 'time', 'qty', 'quantity', 'price', 'amount',
        'phone', 'email', 'address', 'status', 'type', 'code', 'no', 'number',
        'description', 'remark', 'unit', 'spec', 'batch',
    ]
    
    # 非表头特征词 (通常出现在标题/说明行)
    NON_HEADER_KEYWORDS = [
        '导出', '报表', '统计', '汇总', '明细', '清单', '日期:', '时间:',
        '制表', '审核', '打印', '页码', 'page', 'report', 'export',
    ]
    
    @staticmethod
    def detect(file_path: str, max_scan_rows: int = 20) -> Tuple[int, float]:
        """
        检测 Excel 文件的表头行
        
        Args:
            file_path: Excel 文件路径
            max_scan_rows: 最大扫描行数
            
        Returns:
            (row_index, confidence): 表头行号 (0-based) 和置信度 (0-100)
        """
        try:
            # 读取原始数据（不指定表头）
            df_raw = pd.read_excel(file_path, header=None, nrows=max_scan_rows)
        except Exception as e:
            print(f"[HeaderDetector] 读取文件失败: {e}")
            return 0, 50.0  # 默认第一行，中等置信度
        
        if len(df_raw) == 0:
            return 0, 50.0
        
        best_row = 0
        best_score = 0.0
        
        # 扫描每一行
        for row_idx in range(min(max_scan_rows, len(df_raw))):
            score = ExcelHeaderDetector._calculate_row_score(df_raw, row_idx)
            if score > best_score:
                best_score = score
                best_row = row_idx
        
        # 转换为置信度 (0-100)
        confidence = min(best_score, 100.0)
        
        print(f"[HeaderDetector] 检测结果: 第{best_row + 1}行, 置信度: {confidence:.0f}%")
        return best_row, confidence
    
    @staticmethod
    def _calculate_row_score(df: pd.DataFrame, row_idx: int) -> float:
        """
        计算单行的表头可能性评分
        
        Args:
            df: 原始 DataFrame (无表头)
            row_idx: 行索引
            
        Returns:
            评分 (0-100)
        """
        if row_idx >= len(df):
            return 0.0
        
        row = df.iloc[row_idx]
        score = 0.0
        
        # ===== 特征1: 列标题关键词 (+30) =====
        keyword_matches = 0
        for cell in row:
            cell_str = str(cell).lower().strip()
            for keyword in ExcelHeaderDetector.HEADER_KEYWORDS:
                if keyword.lower() in cell_str:
                    keyword_matches += 1
                    break
        
        if keyword_matches > 0:
            # 匹配越多分数越高，最高30分
            keyword_score = min(30, keyword_matches * 10)
            score += keyword_score
        
        # ===== 特征2: 非空比例 (+20) =====
        non_empty_count = sum(1 for cell in row if pd.notna(cell) and str(cell).strip())
        non_empty_ratio = non_empty_count / len(row) if len(row) > 0 else 0
        
        if non_empty_ratio >= 0.8:
            score += 20
        elif non_empty_ratio >= 0.5:
            score += 10
        
        # ===== 特征3: 非纯数字 (+15) =====
        numeric_count = 0
        for cell in row:
            cell_str = str(cell).strip()
            if cell_str and re.match(r'^[\d\.\-,]+$', cell_str):
                numeric_count += 1
        
        numeric_ratio = numeric_count / max(non_empty_count, 1)
        if numeric_ratio < 0.3:  # 大多数不是纯数字
            score += 15
        
        # ===== 特征4: 下方有足够数据行 (+10) =====
        remaining_rows = len(df) - row_idx - 1
        if remaining_rows >= 5:
            score += 10
        elif remaining_rows >= 2:
            score += 5
        
        # ===== 特征5: 数据类型一致性 (+25) =====
        if row_idx < len(df) - 3:  # 至少需要3行数据来判断
            type_consistency = ExcelHeaderDetector._check_type_consistency(df, row_idx)
            score += type_consistency * 25
        
        # ===== 负面特征: 非表头特征词 (-20) =====
        for cell in row:
            cell_str = str(cell).lower()
            for non_kw in ExcelHeaderDetector.NON_HEADER_KEYWORDS:
                if non_kw.lower() in cell_str:
                    score -= 20
                    break
        
        return max(0, score)
    
    @staticmethod
    def _check_type_consistency(df: pd.DataFrame, header_row: int) -> float:
        """
        检查表头下方数据的类型一致性
        
        如果每列的数据类型一致，说明这行很可能是表头。
        
        Returns:
            一致性分数 (0.0 - 1.0)
        """
        data_rows = df.iloc[header_row + 1:header_row + 6]  # 取后5行
        if len(data_rows) < 2:
            return 0.0
        
        consistent_cols = 0
        total_cols = len(df.columns)
        
        for col_idx in range(total_cols):
            col_values = data_rows.iloc[:, col_idx].dropna()
            if len(col_values) < 2:
                continue
            
            # 检查类型一致性
            types = set()
            for val in col_values:
                val_str = str(val).strip()
                if not val_str:
                    continue
                if re.match(r'^[\d\.\-,]+$', val_str):
                    types.add('numeric')
                elif re.match(r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}', val_str):
                    types.add('date')
                else:
                    types.add('text')
            
            if len(types) <= 1:  # 类型一致
                consistent_cols += 1
        
        return consistent_cols / max(total_cols, 1)
    
    @staticmethod
    def get_raw_preview(file_path: str, rows: int = 10) -> pd.DataFrame:
        """
        获取原始预览数据（不指定表头）
        
        Args:
            file_path: Excel 文件路径
            rows: 预览行数
            
        Returns:
            原始 DataFrame（列名为数字索引）
        """
        try:
            return pd.read_excel(file_path, header=None, nrows=rows).fillna("")
        except Exception as e:
            print(f"[HeaderDetector] 预览失败: {e}")
            return pd.DataFrame()
