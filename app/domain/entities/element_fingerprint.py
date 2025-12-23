"""
元素指纹实体

提供 ElementFingerprint 类，用于多维度标识和定位网页元素。
支持自愈选择器和表格行模式分析。

核心功能:
- 多重选择器（ID, XPath, CSS, ARIA）
- 语义锚点（Label, Placeholder, aria-label）
- 表格位置信息
- 稳定性评分
- Iframe 上下文
"""

from typing import Dict, Any, Optional


class ElementFingerprint:
    """
    元素多维指纹
    
    存储网页元素的多维度标识信息，支持选择器自愈和表格模式分析。
    
    Attributes:
        selectors: 多重选择器字典 (id, xpath, css, aria, text)
        anchors: 语义锚点字典 (label, placeholder, aria_label 等)
        features: 元素特征字典 (tag, type, name, class, position)
        table_info: 表格位置信息
        rect: 元素坐标 (x, y, width, height)
        stability_score: 稳定性评分 (0-100)
        frame_info: Iframe 上下文信息
    """
    
    def __init__(self, element_data: Dict[str, Any]) -> None:
        """
        初始化元素指纹
        
        Args:
            element_data: 从 JS 扫描返回的原始数据字典
        """
        self.raw_data: Dict[str, Any] = element_data
        
        # 1. 多重选择器路径
        self.selectors: Dict[str, Optional[str]] = {
            'id': element_data.get('id_selector'),
            'xpath': element_data.get('xpath'),
            'css': element_data.get('css_selector'),
            'aria': element_data.get('aria_selector'),
            'text': element_data.get('text_selector')
        }
        
        # 2. 语义锚点
        self.anchors: Dict[str, str] = {
            'label': element_data.get('label_text', ''),
            'placeholder': element_data.get('placeholder', ''),
            'nearby_text': element_data.get('nearby_text', ''),
            'parent_title': element_data.get('parent_title', ''),
            'visual_label': element_data.get('visual_label', ''),
            'aria_label': element_data.get('aria_label', ''),
            'el_form_label': element_data.get('el_form_label', ''),
            'dialog_context': element_data.get('dialog_context', ''),
        }
        
        # 3. 元素特征
        self.features: Dict[str, Any] = {
            'tag': element_data.get('tagName', ''),
            'type': element_data.get('type', ''),
            'name': element_data.get('name', ''),
            'class': element_data.get('className', ''),
            'position': element_data.get('rect', {})
        }
        
        # 4. 表格位置信息
        self.table_info: Dict[str, Any] = {
            'row_index': element_data.get('row_index'),
            'col_index': element_data.get('col_index'),
            'table_id': element_data.get('table_id'),
            'is_table_cell': element_data.get('is_table_cell', False),
            'table_header': element_data.get('table_header', '')
        }
        
        # 5. 坐标信息
        self.rect: Dict[str, int] = element_data.get('rect', {
            'x': 0, 'y': 0, 'width': 0, 'height': 0
        })
        
        # 6. 稳定性评分
        self.stability_score: int = self._calculate_stability()
        
        # 7. 行模式分析
        self.row_pattern: Dict[str, Any] = element_data.get('row_pattern', {})
        
        # 8. Iframe 上下文
        self.frame_info: Dict[str, Any] = {
            'frame_path': element_data.get('frame_path', ''),
            'frame_src': element_data.get('frame_src', ''),
            'in_iframe': element_data.get('in_iframe', False),
            'frame_depth': element_data.get('frame_depth', 0)
        }
    
    def _calculate_stability(self) -> int:
        """
        计算选择器稳定性评分（100分制）
        
        评分规则:
        - ID选择器: +40分
        - aria-label: +35分
        - Element UI 标签: +25分
        - Name属性: +20分
        - ARIA/Label: +15分
        - CSS类名: +10分
        
        Returns:
            稳定性评分 (0-100)
        """
        score = 0
        
        if self.selectors.get('id'):
            score += 40
        if self.anchors.get('aria_label'):
            score += 35
        if self.anchors.get('el_form_label'):
            score += 25
        if self.features.get('name'):
            score += 20
        if self.anchors.get('label'):
            score += 15
        if self.features.get('class'):
            score += 10
        
        return min(score, 100)
    
    def get_display_name(self) -> str:
        """
        生成人类可读的元素名称
        
        优先级: aria_label > el_form_label > label > placeholder > name > id > [tag]
        
        Returns:
            元素的显示名称
        """
        if self.anchors.get('aria_label'):
            return self.anchors['aria_label']
        if self.anchors.get('el_form_label'):
            return self.anchors['el_form_label']
        if self.anchors.get('label'):
            return self.anchors['label']
        if self.anchors.get('placeholder'):
            return self.anchors['placeholder']
        if self.features.get('name'):
            return self.features['name']
        if self.selectors.get('id'):
            return self.selectors['id'].replace('#', '')
        return f"[{self.features.get('tag', 'unknown')}]"
    
    def get_best_selector(self) -> Optional[str]:
        """
        获取最稳定的选择器
        
        优先级: id > xpath > css > aria > text
        
        Returns:
            最佳选择器字符串，如果都不可用则返回 None
        """
        for key in ['id', 'xpath', 'css', 'aria', 'text']:
            if self.selectors.get(key):
                return self.selectors[key]
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            包含所有指纹信息的字典
        """
        return {
            'selectors': self.selectors,
            'anchors': self.anchors,
            'features': self.features,
            'table_info': self.table_info,
            'rect': self.rect,
            'stability_score': self.stability_score,
            'frame_info': self.frame_info,
            'row_pattern': self.row_pattern,
            'raw_data': self.raw_data,
            'display_name': self.get_display_name()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ElementFingerprint':
        """
        从字典创建 ElementFingerprint 实例
        
        Args:
            data: 包含指纹信息的字典（来自 to_dict 或 JSON 加载）
            
        Returns:
            ElementFingerprint 实例
        """
        # 如果有 raw_data，优先使用
        if 'raw_data' in data and data['raw_data']:
            return cls(data['raw_data'])
        
        # 否则从结构化数据重建 raw_data
        raw_data = {}
        
        # 从 selectors 重建
        if 'selectors' in data:
            raw_data['id_selector'] = data['selectors'].get('id')
            raw_data['xpath'] = data['selectors'].get('xpath')
            raw_data['css_selector'] = data['selectors'].get('css')
            raw_data['aria_selector'] = data['selectors'].get('aria')
            raw_data['text_selector'] = data['selectors'].get('text')
        
        # 从 anchors 重建
        if 'anchors' in data:
            raw_data['label_text'] = data['anchors'].get('label', '')
            raw_data['placeholder'] = data['anchors'].get('placeholder', '')
            raw_data['nearby_text'] = data['anchors'].get('nearby_text', '')
            raw_data['parent_title'] = data['anchors'].get('parent_title', '')
            raw_data['visual_label'] = data['anchors'].get('visual_label', '')
            raw_data['aria_label'] = data['anchors'].get('aria_label', '')
            raw_data['el_form_label'] = data['anchors'].get('el_form_label', '')
            raw_data['dialog_context'] = data['anchors'].get('dialog_context', '')
        
        # 从 features 重建
        if 'features' in data:
            raw_data['tagName'] = data['features'].get('tag', '')
            raw_data['type'] = data['features'].get('type', '')
            raw_data['name'] = data['features'].get('name', '')
            raw_data['className'] = data['features'].get('class', '')
            raw_data['rect'] = data['features'].get('position', {})
        
        # 从 table_info 重建
        if 'table_info' in data:
            raw_data['row_index'] = data['table_info'].get('row_index')
            raw_data['col_index'] = data['table_info'].get('col_index')
            raw_data['table_id'] = data['table_info'].get('table_id')
            raw_data['is_table_cell'] = data['table_info'].get('is_table_cell', False)
            raw_data['table_header'] = data['table_info'].get('table_header', '')
        
        # 从 frame_info 重建
        if 'frame_info' in data:
            raw_data['frame_path'] = data['frame_info'].get('frame_path', '')
            raw_data['frame_src'] = data['frame_info'].get('frame_src', '')
            raw_data['in_iframe'] = data['frame_info'].get('in_iframe', False)
            raw_data['frame_depth'] = data['frame_info'].get('frame_depth', 0)
        
        # 其他字段
        if 'rect' in data:
            raw_data['rect'] = data['rect']
        if 'row_pattern' in data:
            raw_data['row_pattern'] = data['row_pattern']
        
        return cls(raw_data)
    
    def get_selector_for_row(self, row_index: int) -> Optional[tuple]:
        """
        获取指定行的动态选择器
        
        用于表格模式下，根据行号生成对应行的选择器。
        
        Args:
            row_index: 目标行索引 (0-based)
            
        Returns:
            ('xpath', selector_string) 或 ('css', selector_string) 或 None
        """
        import re
        
        xpath = self.selectors.get('xpath', '')
        if not xpath:
            return None
        
        # 策略1: 检查是否包含行号模式 tr[N] 或 tbody/tr[N]
        if re.search(r'tr\[\d+\]', xpath):
            # 替换行号 (1-based in XPath)
            dynamic_xpath = re.sub(r'tr\[\d+\]', f'tr[{row_index + 1}]', xpath)
            return ('xpath', dynamic_xpath)
        
        # 策略2: 检查是否包含 row 类模式 div[N] 或带有 row 的 div
        if re.search(r'div\[\d+\]', xpath) and 'row' in xpath.lower():
            dynamic_xpath = re.sub(r'div\[\d+\]', f'div[{row_index + 1}]', xpath)
            return ('xpath', dynamic_xpath)
        
        # 策略3: 使用 table_info 中的表格位置信息
        if self.table_info.get('is_table_element'):
            # 尝试构建基于表格位置的选择器
            col_index = self.table_info.get('column_index', 0)
            
            # 检查是否有表格 ID 或类名可用
            if 'table' in xpath.lower():
                # 尝试在 XPath 中插入行索引
                # 例如: //table/tbody/tr/td[2] -> //table/tbody/tr[N+1]/td[2]
                if '/tr/' in xpath and '/td' in xpath:
                    dynamic_xpath = xpath.replace('/tr/', f'/tr[{row_index + 1}]/', 1)
                    return ('xpath', dynamic_xpath)
                elif '//tr/' in xpath and '/td' in xpath:
                    dynamic_xpath = xpath.replace('//tr/', f'//tr[{row_index + 1}]/', 1)
                    return ('xpath', dynamic_xpath)
        
        # 策略4: 如果没有可识别的模式，返回原始选择器（不做行替换）
        # 这意味着所有行都会填充到同一个元素（原始扫描到的元素）
        return ('xpath', xpath)
    
    def __repr__(self) -> str:
        return f"<ElementFingerprint: {self.get_display_name()} (score={self.stability_score})>"
