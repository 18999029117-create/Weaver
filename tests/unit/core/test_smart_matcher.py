"""
SmartMatcher 单元测试

测试智能字段匹配器的核心功能。
"""

import pytest
from app.core.smart_matcher import SmartMatcher
from app.domain.entities import ElementFingerprint


class TestSmartMatcher:
    """SmartMatcher 测试套件"""
    
    # ==================== 匹配分数计算测试 ====================
    
    def test_exact_match_returns_100_score(self, fingerprint):
        """精确匹配应返回 100 分"""
        # fingerprint 的 label 是 "用户名"
        score = SmartMatcher._calculate_match_score('用户名', fingerprint)
        assert score == 100
    
    def test_partial_match_returns_expected_score(self, sample_element_data):
        """部分匹配应返回 40-80 分"""
        fp = ElementFingerprint(sample_element_data)
        # "用户" 是 "用户名" 的部分匹配
        score = SmartMatcher._calculate_match_score('用户', fp)
        assert 40 <= score <= 80
    
    def test_no_match_returns_zero_score(self, fingerprint):
        """无匹配应返回 0 分"""
        score = SmartMatcher._calculate_match_score('完全不相关的字段', fingerprint)
        assert score == 0
    
    def test_placeholder_match(self, sample_element_data):
        """placeholder 匹配测试"""
        fp = ElementFingerprint(sample_element_data)
        # placeholder 是 "请输入用户名"
        score = SmartMatcher._calculate_match_score('请输入用户名', fp)
        assert score >= 60
    
    def test_name_attribute_match(self, sample_element_data):
        """name 属性匹配测试"""
        fp = ElementFingerprint(sample_element_data)
        # name 是 "username"
        score = SmartMatcher._calculate_match_score('username', fp)
        assert score >= 60
    
    # ==================== 字段匹配测试 ====================
    
    def test_match_fields_returns_correct_structure(self, excel_columns, web_fingerprints):
        """match_fields 应返回正确的数据结构"""
        result = SmartMatcher.match_fields(excel_columns, web_fingerprints)
        
        assert 'matched' in result
        assert 'unmatched_excel' in result
        assert 'unmatched_web' in result
        
        assert isinstance(result['matched'], list)
        assert isinstance(result['unmatched_excel'], list)
        assert isinstance(result['unmatched_web'], list)
    
    def test_match_fields_successful_matches(self, excel_columns, web_fingerprints):
        """成功匹配的字段应出现在 matched 中"""
        result = SmartMatcher.match_fields(excel_columns, web_fingerprints)
        
        matched_excel_cols = [item[0] for item in result['matched']]
        
        # '用户名' 应该匹配到 username fingerprint
        assert '用户名' in matched_excel_cols
        # '密码' 应该匹配到 password fingerprint
        assert '密码' in matched_excel_cols
    
    def test_match_fields_unmatched_columns(self, excel_columns, web_fingerprints):
        """未匹配的 Excel 列应出现在 unmatched_excel 中"""
        result = SmartMatcher.match_fields(excel_columns, web_fingerprints)
        
        # 'HIS编码' 没有对应的网页元素
        assert 'HIS编码' in result['unmatched_excel']
    
    def test_match_fields_uses_fingerprints_once(self, excel_columns, web_fingerprints):
        """每个 fingerprint 只能匹配一个 Excel 列"""
        result = SmartMatcher.match_fields(excel_columns, web_fingerprints)
        
        matched_fingerprints = [item[1] for item in result['matched']]
        matched_ids = [id(fp) for fp in matched_fingerprints]
        
        # 确保没有重复使用的 fingerprint
        assert len(matched_ids) == len(set(matched_ids))
    
    # ==================== 文本处理测试 ====================
    
    def test_normalize_text_removes_punctuation(self):
        """规范化应去除标点符号"""
        result = SmartMatcher._normalize_text('用户名：')
        assert result == '用户名'
    
    def test_normalize_text_converts_to_lowercase(self):
        """规范化应转换为小写"""
        result = SmartMatcher._normalize_text('UserName')
        assert result == 'username'
    
    def test_normalize_text_removes_spaces(self):
        """规范化应去除空格"""
        result = SmartMatcher._normalize_text('User Name')
        assert result == 'username'
    
    def test_normalize_text_handles_empty_string(self):
        """规范化应处理空字符串"""
        result = SmartMatcher._normalize_text('')
        assert result == ''
    
    def test_normalize_text_handles_none(self):
        """规范化应处理 None"""
        result = SmartMatcher._normalize_text(None)
        assert result == ''
    
    # ==================== 分词测试 ====================
    
    def test_split_words_camel_case(self):
        """分词应处理驼峰命名"""
        result = SmartMatcher._split_words('userName')
        assert 'user' in result
        assert 'name' in result
    
    def test_split_words_underscore(self):
        """分词应处理下划线分隔"""
        result = SmartMatcher._split_words('user_name')
        assert 'user' in result
        assert 'name' in result
    
    def test_split_words_hyphen(self):
        """分词应处理连字符分隔"""
        result = SmartMatcher._split_words('user-name')
        assert 'user' in result
        assert 'name' in result
    
    def test_split_words_handles_empty_string(self):
        """分词应处理空字符串"""
        result = SmartMatcher._split_words('')
        assert result == []
    
    def test_split_words_handles_none(self):
        """分词应处理 None"""
        result = SmartMatcher._split_words(None)
        assert result == []


class TestSmartMatcherEdgeCases:
    """SmartMatcher 边界情况测试"""
    
    def test_empty_excel_columns(self, web_fingerprints):
        """空 Excel 列列表"""
        result = SmartMatcher.match_fields([], web_fingerprints)
        
        assert result['matched'] == []
        assert result['unmatched_excel'] == []
        assert len(result['unmatched_web']) == len(web_fingerprints)
    
    def test_empty_web_fingerprints(self, excel_columns):
        """空网页指纹列表"""
        result = SmartMatcher.match_fields(excel_columns, [])
        
        assert result['matched'] == []
        assert result['unmatched_web'] == []
        assert result['unmatched_excel'] == excel_columns
    
    def test_both_empty(self):
        """两者都为空"""
        result = SmartMatcher.match_fields([], [])
        
        assert result['matched'] == []
        assert result['unmatched_excel'] == []
        assert result['unmatched_web'] == []
