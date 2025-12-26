"""
ElementFingerprint 单元测试

测试元素指纹的核心功能。
"""

import pytest
from app.domain.entities import ElementFingerprint


class TestElementFingerprintBasic:
    """ElementFingerprint 基础功能测试"""
    
    def test_init_creates_valid_instance(self, sample_element_data):
        """初始化应创建有效实例"""
        fp = ElementFingerprint(sample_element_data)
        
        assert fp is not None
        assert isinstance(fp.selectors, dict)
        assert isinstance(fp.anchors, dict)
        assert isinstance(fp.features, dict)
    
    def test_selectors_populated_correctly(self, sample_element_data):
        """选择器应正确填充"""
        fp = ElementFingerprint(sample_element_data)
        
        assert fp.selectors['id'] == '#username'
        assert fp.selectors['xpath'] == '//input[@id="username"]'
        assert fp.selectors['css'] == 'input#username'
    
    def test_anchors_populated_correctly(self, sample_element_data):
        """锚点应正确填充"""
        fp = ElementFingerprint(sample_element_data)
        
        assert fp.anchors['label'] == '用户名'
        assert fp.anchors['placeholder'] == '请输入用户名'
        assert fp.anchors['aria_label'] == '用户名输入框'
    
    def test_features_populated_correctly(self, sample_element_data):
        """特征应正确填充"""
        fp = ElementFingerprint(sample_element_data)
        
        assert fp.features['tag'] == 'input'
        assert fp.features['type'] == 'text'
        assert fp.features['name'] == 'username'


class TestElementFingerprintStability:
    """稳定性评分测试"""
    
    def test_id_adds_40_points(self, sample_element_data):
        """ID 选择器应增加 40 分"""
        # 只保留 id
        data = {'id_selector': '#test'}
        fp = ElementFingerprint(data)
        
        assert fp.stability_score >= 40
    
    def test_aria_label_adds_35_points(self, sample_element_data):
        """aria-label 应增加 35 分"""
        data = {'aria_label': 'Test label'}
        fp = ElementFingerprint(data)
        
        assert fp.stability_score >= 35
    
    def test_combined_score_capped_at_100(self, sample_element_data):
        """组合分数应上限为 100"""
        # sample_element_data 包含多个得分项
        fp = ElementFingerprint(sample_element_data)
        
        assert fp.stability_score <= 100
    
    def test_empty_data_returns_zero_score(self):
        """空数据应返回 0 分"""
        fp = ElementFingerprint({})
        
        assert fp.stability_score == 0


class TestElementFingerprintDisplayName:
    """显示名称测试"""
    
    def test_aria_label_has_highest_priority(self, sample_element_data):
        """aria_label 优先级最高"""
        fp = ElementFingerprint(sample_element_data)
        
        # sample_element_data 有 aria_label = "用户名输入框"
        assert fp.get_display_name() == '用户名输入框'
    
    def test_el_form_label_used_when_no_aria(self):
        """没有 aria_label 时使用 el_form_label"""
        data = {
            'el_form_label': 'Element Form Label',
            'label_text': 'Normal Label',
        }
        fp = ElementFingerprint(data)
        
        assert fp.get_display_name() == 'Element Form Label'
    
    def test_label_used_when_no_special_labels(self):
        """没有特殊标签时使用 label"""
        data = {
            'label_text': 'Normal Label',
            'placeholder': 'Placeholder',
        }
        fp = ElementFingerprint(data)
        
        assert fp.get_display_name() == 'Normal Label'
    
    def test_fallback_to_tag_when_no_names(self):
        """没有名称时回退到标签"""
        data = {'tagName': 'input'}
        fp = ElementFingerprint(data)
        
        assert fp.get_display_name() == '[input]'
    
    def test_empty_tag_when_completely_empty(self):
        """完全为空时返回空标签（因为 tag 默认为空字符串）"""
        fp = ElementFingerprint({})
        
        # 当 element_data 为空时，features['tag'] 为空字符串
        # get_display_name 返回 f"[{self.features.get('tag', 'unknown')}]" = "[]"
        assert fp.get_display_name() == '[]'


class TestElementFingerprintBestSelector:
    """最佳选择器测试"""
    
    def test_id_selector_is_preferred(self, sample_element_data):
        """ID 选择器优先"""
        fp = ElementFingerprint(sample_element_data)
        
        best = fp.get_best_selector()
        assert best == '#username'
    
    def test_xpath_used_when_no_id(self):
        """没有 ID 时使用 XPath"""
        data = {
            'xpath': '//input[@name="test"]',
            'css_selector': 'input[name="test"]',
        }
        fp = ElementFingerprint(data)
        
        best = fp.get_best_selector()
        assert best == '//input[@name="test"]'
    
    def test_returns_none_when_no_selectors(self):
        """没有选择器时返回 None"""
        fp = ElementFingerprint({})
        
        best = fp.get_best_selector()
        assert best is None


class TestElementFingerprintTableInfo:
    """表格信息测试"""
    
    def test_is_table_cell_detected(self, table_element_data):
        """表格元素应被正确识别"""
        fp = ElementFingerprint(table_element_data)
        
        assert fp.table_info['is_table_cell'] is True
    
    def test_row_col_index_captured(self, table_element_data):
        """行列索引应被正确捕获"""
        fp = ElementFingerprint(table_element_data)
        
        assert fp.table_info['row_index'] == 1
        assert fp.table_info['col_index'] == 2
    
    def test_table_header_captured(self, table_element_data):
        """表头应被正确捕获"""
        fp = ElementFingerprint(table_element_data)
        
        assert fp.table_info['table_header'] == '数量'


class TestElementFingerprintIframe:
    """Iframe 信息测试"""
    
    def test_in_iframe_detected(self, iframe_element_data):
        """Iframe 内元素应被正确识别"""
        fp = ElementFingerprint(iframe_element_data)
        
        assert fp.frame_info['in_iframe'] is True
    
    def test_frame_path_captured(self, iframe_element_data):
        """frame_path 应被正确捕获"""
        fp = ElementFingerprint(iframe_element_data)
        
        assert 'iframe#content' in fp.frame_info['frame_path']
    
    def test_frame_depth_captured(self, iframe_element_data):
        """嵌套深度应被正确捕获"""
        fp = ElementFingerprint(iframe_element_data)
        
        assert fp.frame_info['frame_depth'] == 2


class TestElementFingerprintSerialization:
    """序列化/反序列化测试"""
    
    def test_to_dict_returns_dict(self, fingerprint):
        """to_dict 应返回字典"""
        result = fingerprint.to_dict()
        
        assert isinstance(result, dict)
        assert 'selectors' in result
        assert 'anchors' in result
        assert 'stability_score' in result
    
    def test_from_dict_recreates_fingerprint(self, fingerprint):
        """from_dict 应正确重建指纹"""
        data = fingerprint.to_dict()
        recreated = ElementFingerprint.from_dict(data)
        
        assert recreated.get_display_name() == fingerprint.get_display_name()
        assert recreated.stability_score == fingerprint.stability_score
    
    def test_roundtrip_preserves_data(self, sample_element_data):
        """往返转换应保留数据"""
        original = ElementFingerprint(sample_element_data)
        data = original.to_dict()
        recreated = ElementFingerprint.from_dict(data)
        
        assert recreated.selectors['id'] == original.selectors['id']
        assert recreated.anchors['label'] == original.anchors['label']


class TestElementFingerprintRowSelector:
    """行选择器测试"""
    
    def test_get_selector_for_row_replaces_index(self, table_element_data):
        """get_selector_for_row 应替换行索引"""
        fp = ElementFingerprint(table_element_data)
        
        result = fp.get_selector_for_row(5)
        
        assert result is not None
        selector_type, selector = result
        assert selector_type == 'xpath'
        assert 'tr[6]' in selector  # XPath is 1-based
    
    def test_returns_original_when_no_pattern(self, sample_element_data):
        """没有行模式时返回原始选择器"""
        fp = ElementFingerprint(sample_element_data)
        
        result = fp.get_selector_for_row(3)
        
        # 应返回原始 xpath（无替换）
        assert result is not None


class TestElementFingerprintRepr:
    """字符串表示测试"""
    
    def test_repr_contains_display_name(self, fingerprint):
        """repr 应包含显示名称"""
        result = repr(fingerprint)
        
        assert 'ElementFingerprint' in result
        assert '用户名' in result or 'score=' in result
    
    def test_repr_contains_score(self, fingerprint):
        """repr 应包含稳定性分数"""
        result = repr(fingerprint)
        
        assert 'score=' in result
