"""
锚定匹配器 - 自动匹配 Excel 列和网页列

实现多重锚定匹配功能的核心逻辑。
遵循 CONTRIBUTING.md 中的代码规范。
"""

from typing import List, Dict, Optional
from difflib import SequenceMatcher

from app.domain.entities.anchor_config import (
    AnchorPair, 
    AnchorConfig, 
    WebColumnInfo
)


class AnchorMatcher:
    """
    锚定匹配器
    
    职责:
    - 自动匹配 Excel 列名和网页列标题
    - 区分锚定列（只读）和待填列（输入框）
    - 计算匹配置信度
    """
    
    # 排除的通用列名（不适合作为锚定列）
    EXCLUDE_ANCHOR_KEYWORDS = [
        '操作', '选择', '序号', '编号', 'action', 'select', 'index',
        '备注', 'remark', 'note', '说明'
    ]
    
    # 排除的待填列名（通常是只读数据）
    EXCLUDE_FILL_KEYWORDS = [
        '编码', '名称', '规格', '单位', '厂家', '科室', 
        'code', 'name', 'spec', 'unit', 'manufacturer'
    ]
    
    @staticmethod
    def calculate_similarity(str1: str, str2: str) -> float:
        """
        计算两个字符串的相似度
        
        Args:
            str1: 字符串1
            str2: 字符串2
            
        Returns:
            相似度分数 (0.0 - 1.0)
        """
        if not str1 or not str2:
            return 0.0
        
        # 预处理：统一小写，去除空白
        s1 = str1.lower().strip()
        s2 = str2.lower().strip()
        
        # 完全匹配
        if s1 == s2:
            return 1.0
        
        # 包含关系
        if s1 in s2 or s2 in s1:
            return 0.9
        
        # 序列匹配
        return SequenceMatcher(None, s1, s2).ratio()
    
    @staticmethod
    def auto_match(
        excel_columns: List[str],
        web_columns: List[WebColumnInfo],
        threshold: float = 0.6
    ) -> AnchorConfig:
        """
        自动匹配 Excel 列和网页列
        
        匹配策略:
        1. 只读网页列 → 锚定列候选
        2. 输入框网页列 → 待填列候选
        3. 使用列名相似度进行配对
        
        Args:
            excel_columns: Excel 列名列表
            web_columns: 网页列信息列表
            threshold: 相似度阈值（默认0.6）
            
        Returns:
            AnchorConfig: 自动生成的锚定配置
        """
        config = AnchorConfig(auto_matched=True)
        
        # 分离只读列和输入框列
        readonly_cols = [c for c in web_columns if c.is_readonly]
        input_cols = [c for c in web_columns if c.is_input]
        
        print(f"\n=== 🔗 自动匹配开始 ===")
        print(f"   Excel 列数: {len(excel_columns)}")
        print(f"   网页只读列: {len(readonly_cols)}")
        print(f"   网页输入列: {len(input_cols)}")
        
        total_score = 0.0
        match_count = 0
        
        # 1. 匹配锚定列（Excel 列 ↔ 网页只读列）
        for excel_col in excel_columns:
            # 跳过不适合作为锚定列的列名
            if AnchorMatcher._should_exclude_anchor(excel_col):
                continue
            
            best_match = None
            best_score = 0.0
            
            for web_col in readonly_cols:
                score = AnchorMatcher.calculate_similarity(excel_col, web_col.label)
                if score > best_score and score >= threshold:
                    best_score = score
                    best_match = web_col
            
            if best_match:
                config.add_anchor_pair(
                    excel_col=excel_col,
                    web_xpath=best_match.xpath,
                    web_label=best_match.label
                )
                total_score += best_score
                match_count += 1
                print(f"   ✅ 锚定: {excel_col} ↔ {best_match.label} (相似度:{best_score:.0%})")
        
        # 2. 匹配待填列（Excel 列 ↔ 网页输入列）
        for excel_col in excel_columns:
            # 跳过已作为锚定列的
            if excel_col in config.get_excel_anchor_columns():
                continue
            
            # 跳过不适合作为待填列的列名
            if AnchorMatcher._should_exclude_fill(excel_col):
                continue
            
            best_match = None
            best_score = 0.0
            
            for web_col in input_cols:
                score = AnchorMatcher.calculate_similarity(excel_col, web_col.label)
                if score > best_score and score >= threshold:
                    best_score = score
                    best_match = web_col
            
            if best_match:
                # 待填列存储到 fill_mappings（保留接口兼容）
                config.fill_mappings[excel_col] = {
                    'web_label': best_match.label,
                    'web_xpath': best_match.xpath
                }
                total_score += best_score
                match_count += 1
                print(f"   📝 待填: {excel_col} → {best_match.label} (相似度:{best_score:.0%})")
        
        # 计算整体置信度
        if match_count > 0:
            config.match_confidence = (total_score / match_count) * 100
        
        print(f"\n   📊 匹配结果: {config.anchor_count} 个锚定列, {len(config.fill_mappings)} 个待填列")
        print(f"   📊 置信度: {config.match_confidence:.0f}%")
        print(f"=== 🔗 自动匹配完成 ===\n")
        
        return config
    
    @staticmethod
    def _should_exclude_anchor(column_name: str) -> bool:
        """检查列名是否应排除作为锚定列"""
        lower_name = column_name.lower()
        return any(kw in lower_name for kw in AnchorMatcher.EXCLUDE_ANCHOR_KEYWORDS)
    
    @staticmethod
    def _should_exclude_fill(column_name: str) -> bool:
        """检查列名是否应排除作为待填列"""
        lower_name = column_name.lower()
        return any(kw in lower_name for kw in AnchorMatcher.EXCLUDE_FILL_KEYWORDS)
    
    @staticmethod
    def validate_anchor_config(
        config: AnchorConfig,
        excel_columns: List[str],
        web_columns: List[WebColumnInfo]
    ) -> List[str]:
        """
        验证锚定配置的有效性
        
        Returns:
            错误消息列表（空列表表示配置有效）
        """
        errors = []
        
        # 检查是否有锚定列
        if config.anchor_count == 0:
            errors.append("至少需要配置一个锚定列")
        
        # 检查锚定列是否存在于 Excel
        for pair in config.enabled_anchors:
            if pair.excel_column not in excel_columns:
                errors.append(f"锚定列 '{pair.excel_column}' 在 Excel 中不存在")
        
        # 检查是否有待填列
        if len(config.fill_mappings) == 0:
            errors.append("至少需要配置一个待填列")
        
        return errors
