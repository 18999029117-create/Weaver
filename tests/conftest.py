"""
Pytest 配置文件

提供测试所需的 fixtures 和共享配置。
"""

import sys
from pathlib import Path

import pytest

# 确保项目根目录在 Python 路径中
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# ElementFingerprint Fixtures
# ============================================================

@pytest.fixture
def sample_element_data():
    """基础元素数据样本"""
    return {
        'id_selector': '#username',
        'xpath': '//input[@id="username"]',
        'css_selector': 'input#username',
        'tagName': 'input',
        'type': 'text',
        'name': 'username',
        'className': 'el-input__inner',
        'placeholder': '请输入用户名',
        'label_text': '用户名',
        'aria_label': '用户名输入框',
        'el_form_label': '用户名',
        'rect': {'x': 100, 'y': 200, 'width': 200, 'height': 32},
        'row_index': None,
        'col_index': None,
        'is_table_cell': False,
    }


@pytest.fixture
def table_element_data():
    """表格内元素数据样本"""
    return {
        'id_selector': None,
        'xpath': '//table/tbody/tr[2]/td[3]//input',
        'css_selector': 'table tbody tr:nth-child(2) td:nth-child(3) input',
        'tagName': 'input',
        'type': 'text',
        'name': 'qty',
        'className': 'el-input__inner',
        'placeholder': '',
        'label_text': '数量',
        'table_header': '数量',
        'row_index': 1,
        'col_index': 2,
        'table_id': 'main_table',
        'is_table_cell': True,
        'rect': {'x': 300, 'y': 150, 'width': 80, 'height': 28},
    }


@pytest.fixture
def iframe_element_data():
    """Iframe 内元素数据样本"""
    return {
        'xpath': '//input[@name="patient_id"]',
        'css_selector': 'input[name="patient_id"]',
        'tagName': 'input',
        'type': 'text',
        'name': 'patient_id',
        'placeholder': '患者ID',
        'label_text': '患者ID',
        'in_iframe': True,
        'frame_path': 'iframe#content > iframe.inner',
        'frame_src': '/patient/form.html',
        'frame_depth': 2,
        'rect': {'x': 50, 'y': 100, 'width': 150, 'height': 30},
    }


@pytest.fixture
def fingerprint(sample_element_data):
    """ElementFingerprint 实例"""
    from app.domain.entities import ElementFingerprint
    return ElementFingerprint(sample_element_data)


@pytest.fixture
def table_fingerprint(table_element_data):
    """表格元素 ElementFingerprint 实例"""
    from app.domain.entities import ElementFingerprint
    return ElementFingerprint(table_element_data)


# ============================================================
# SmartMatcher Fixtures
# ============================================================

@pytest.fixture
def excel_columns():
    """Excel 列名样本"""
    return ['用户名', '密码', '邮箱', 'HIS编码', '数量']


@pytest.fixture
def web_fingerprints(sample_element_data, table_element_data):
    """网页元素指纹列表样本"""
    from app.domain.entities import ElementFingerprint
    
    # 创建多个指纹
    fp1 = ElementFingerprint(sample_element_data)
    
    # 密码框
    password_data = sample_element_data.copy()
    password_data.update({
        'id_selector': '#password',
        'name': 'password',
        'type': 'password',
        'placeholder': '请输入密码',
        'label_text': '密码',
        'el_form_label': '密码',
    })
    fp2 = ElementFingerprint(password_data)
    
    # 邮箱框
    email_data = sample_element_data.copy()
    email_data.update({
        'id_selector': '#email',
        'name': 'email',
        'type': 'email',
        'placeholder': '请输入邮箱',
        'label_text': '电子邮箱',
        'el_form_label': '邮箱',
    })
    fp3 = ElementFingerprint(email_data)
    
    # 表格元素
    fp4 = ElementFingerprint(table_element_data)
    
    return [fp1, fp2, fp3, fp4]


# ============================================================
# Mock Browser Tab
# ============================================================

class MockBrowserTab:
    """模拟浏览器标签页，用于测试"""
    
    def __init__(self):
        self.js_results = {}
        self.elements = {}
    
    def run_js(self, script):
        """执行 JS 脚本（返回预设结果）"""
        return self.js_results.get(script, None)
    
    def ele(self, selector, timeout=None):
        """查找元素"""
        return self.elements.get(selector, None)
    
    def eles(self, selector):
        """查找多个元素"""
        return self.elements.get(selector, [])


@pytest.fixture
def mock_tab():
    """模拟浏览器标签页"""
    return MockBrowserTab()


# ============================================================
# Test Utilities
# ============================================================

@pytest.fixture
def capture_logs(capsys):
    """捕获日志输出"""
    def _capture():
        captured = capsys.readouterr()
        return captured.out
    return _capture
