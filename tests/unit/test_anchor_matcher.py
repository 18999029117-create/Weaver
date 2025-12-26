"""
AnchorMatcher 锚定匹配器单元测试

测试覆盖:
- 相似度计算
- 自动匹配
- 列名排除规则
- 配置验证
"""

import pytest
from app.core.anchor_matcher import AnchorMatcher
from app.domain.entities.anchor_config import (
    AnchorConfig,
    AnchorPair,
    WebColumnInfo
)


# ============================================================
# 相似度计算测试
# ============================================================

class TestCalculateSimilarity:
    """相似度计算测试"""
    
    def test_exact_match_returns_1(self):
        """完全相同返回 1.0"""
        score = AnchorMatcher.calculate_similarity("用户名", "用户名")
        assert score == 1.0
    
    def test_case_insensitive(self):
        """大小写不敏感"""
        score = AnchorMatcher.calculate_similarity("UserName", "username")
        assert score == 1.0
    
    def test_contains_returns_high_score(self):
        """包含关系返回高分 (0.9)"""
        score = AnchorMatcher.calculate_similarity("姓名", "患者姓名")
        assert score == 0.9
    
    def test_partial_similarity(self):
        """部分相似返回中等分数"""
        score = AnchorMatcher.calculate_similarity("用户", "客户")
        assert 0 < score < 1.0
    
    def test_no_similarity(self):
        """无相似返回低分"""
        score = AnchorMatcher.calculate_similarity("完全", "不同")
        assert score < 0.5
    
    def test_empty_string_returns_0(self):
        """空字符串返回 0"""
        assert AnchorMatcher.calculate_similarity("", "test") == 0.0
        assert AnchorMatcher.calculate_similarity("test", "") == 0.0
        assert AnchorMatcher.calculate_similarity("", "") == 0.0
    
    def test_none_returns_0(self):
        """None 返回 0"""
        assert AnchorMatcher.calculate_similarity(None, "test") == 0.0
        assert AnchorMatcher.calculate_similarity("test", None) == 0.0


# ============================================================
# 排除规则测试
# ============================================================

class TestExcludeRules:
    """列名排除规则测试"""
    
    def test_exclude_anchor_operation_columns(self):
        """排除操作列作为锚定"""
        assert AnchorMatcher._should_exclude_anchor("操作") is True
        assert AnchorMatcher._should_exclude_anchor("选择") is True
        assert AnchorMatcher._should_exclude_anchor("序号") is True
    
    def test_exclude_anchor_case_insensitive(self):
        """排除规则大小写不敏感"""
        assert AnchorMatcher._should_exclude_anchor("ACTION") is True
        assert AnchorMatcher._should_exclude_anchor("Select") is True
    
    def test_normal_columns_not_excluded(self):
        """正常列名不被排除"""
        assert AnchorMatcher._should_exclude_anchor("姓名") is False
        assert AnchorMatcher._should_exclude_anchor("HIS编码") is False
    
    def test_exclude_fill_readonly_columns(self):
        """排除只读列作为待填"""
        assert AnchorMatcher._should_exclude_fill("编码") is True
        assert AnchorMatcher._should_exclude_fill("规格") is True
    
    def test_input_columns_not_excluded(self):
        """输入列不被排除"""
        assert AnchorMatcher._should_exclude_fill("数量") is False
        assert AnchorMatcher._should_exclude_fill("批次") is False


# ============================================================
# 自动匹配测试
# ============================================================

class TestAutoMatch:
    """自动匹配测试"""
    
    @pytest.fixture
    def excel_columns(self):
        """Excel 列名"""
        return ["HIS编码", "名称", "数量", "单价"]
    
    @pytest.fixture
    def web_columns(self):
        """网页列信息"""
        return [
            WebColumnInfo(label="HIS编码", xpath="//td[1]", is_readonly=True, is_input=False),
            WebColumnInfo(label="药品名称", xpath="//td[2]", is_readonly=True, is_input=False),
            WebColumnInfo(label="数量", xpath="//td[3]//input", is_readonly=False, is_input=True),
            WebColumnInfo(label="单价", xpath="//td[4]//input", is_readonly=False, is_input=True),
        ]
    
    def test_auto_match_returns_config(self, excel_columns, web_columns):
        """返回 AnchorConfig"""
        result = AnchorMatcher.auto_match(excel_columns, web_columns)
        
        assert isinstance(result, AnchorConfig)
        assert result.auto_matched is True
    
    def test_matches_anchor_columns(self, excel_columns, web_columns):
        """匹配锚定列"""
        result = AnchorMatcher.auto_match(excel_columns, web_columns)
        
        # HIS编码 应该被匹配为锚定列
        anchor_excels = result.get_excel_anchor_columns()
        assert "HIS编码" in anchor_excels
    
    def test_matches_fill_columns(self, excel_columns, web_columns):
        """匹配待填列"""
        result = AnchorMatcher.auto_match(excel_columns, web_columns)
        
        # 数量和单价应该在待填列中
        assert "数量" in result.fill_mappings or "单价" in result.fill_mappings
    
    def test_confidence_score_calculated(self, excel_columns, web_columns):
        """计算置信度"""
        result = AnchorMatcher.auto_match(excel_columns, web_columns)
        
        # 应该有置信度分数
        assert result.match_confidence >= 0
        assert result.match_confidence <= 100
    
    def test_empty_columns_returns_empty_config(self):
        """空列返回空配置"""
        result = AnchorMatcher.auto_match([], [])
        
        assert result.anchor_count == 0
        assert len(result.fill_mappings) == 0


# ============================================================
# 配置验证测试
# ============================================================

class TestValidateConfig:
    """配置验证测试"""
    
    def test_valid_config_returns_empty(self):
        """有效配置返回空错误列表"""
        config = AnchorConfig()
        config.add_anchor_pair("HIS编码", "//td[1]", "HIS编码")
        config.fill_mappings["数量"] = {"web_label": "数量"}
        
        excel_cols = ["HIS编码", "数量"]
        web_cols = [
            WebColumnInfo(label="HIS编码", xpath="//td[1]", is_readonly=True),
        ]
        
        errors = AnchorMatcher.validate_anchor_config(config, excel_cols, web_cols)
        
        assert len(errors) == 0
    
    def test_no_anchor_returns_error(self):
        """无锚定列返回错误"""
        config = AnchorConfig()
        config.fill_mappings["数量"] = {"web_label": "数量"}
        
        errors = AnchorMatcher.validate_anchor_config(config, [], [])
        
        assert any("锚定列" in e for e in errors)
    
    def test_no_fill_returns_error(self):
        """无待填列返回错误"""
        config = AnchorConfig()
        config.add_anchor_pair("HIS编码", "//td[1]", "HIS编码")
        
        errors = AnchorMatcher.validate_anchor_config(config, ["HIS编码"], [])
        
        assert any("待填列" in e for e in errors)
    
    def test_missing_excel_column_returns_error(self):
        """锚定列不在 Excel 中返回错误"""
        config = AnchorConfig()
        config.add_anchor_pair("不存在的列", "//td[1]", "不存在的列")
        config.fill_mappings["数量"] = {"web_label": "数量"}
        
        errors = AnchorMatcher.validate_anchor_config(config, ["数量"], [])
        
        assert any("不存在" in e for e in errors)
