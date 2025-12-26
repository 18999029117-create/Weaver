"""
锚点解析器

将 Excel 数据预处理为填充队列，解耦锚点匹配与填充执行。
"""

from typing import Dict, Any, Optional, List
import pandas as pd

from app.domain.entities.fill_task import FillTask
from app.core.fill_queue import FillQueue


class AnchorResolver:
    """
    锚点解析器
    
    负责将 Excel 数据转换为 FillQueue，处理锚点匹配逻辑。
    
    - 无锚点: excel_row_idx == web_row_idx (顺序对应)
    - 有锚点: 根据锚点列值匹配网页行
    """
    
    def __init__(self, tab=None):
        """
        Args:
            tab: DrissionPage tab 对象（用于扫描网页锚点值）
        """
        self.tab = tab
    
    def resolve(
        self,
        excel_data: pd.DataFrame,
        fingerprint_mappings: Dict[str, Any],
        anchor_column: Optional[str] = None
    ) -> FillQueue:
        """
        解析 Excel 数据生成填充队列
        
        Args:
            excel_data: Excel 数据 DataFrame
            fingerprint_mappings: 字段映射 {excel_col: fingerprint}
            anchor_column: 锚点列名（可选）
            
        Returns:
            FillQueue: 填充任务队列
        """
        tasks = []
        
        if anchor_column and anchor_column in fingerprint_mappings:
            # 有锚点模式：需要匹配网页中的锚点值
            web_anchor_map = self._scan_web_anchors(fingerprint_mappings[anchor_column])
            
            for excel_idx, row in excel_data.iterrows():
                anchor_value = str(row.get(anchor_column, '')).strip()
                row_data = row.to_dict()
                
                if anchor_value in web_anchor_map:
                    web_idx = web_anchor_map[anchor_value]
                    task = FillTask(
                        excel_row_idx=excel_idx,
                        web_row_idx=web_idx,
                        row_data=row_data,
                        anchor_value=anchor_value
                    )
                else:
                    # 锚点未匹配，标记为跳过
                    task = FillTask(
                        excel_row_idx=excel_idx,
                        web_row_idx=-1,  # 无效索引
                        row_data=row_data,
                        anchor_value=anchor_value
                    )
                    task.mark_skipped(f"锚点值 '{anchor_value}' 未在网页中找到")
                
                tasks.append(task)
        else:
            # 无锚点模式：顺序对应
            # 使用 enumerate 获取从 0 开始的顺序索引，确保 Excel 第1行 → 网页第1个输入框
            for seq_idx, (excel_idx, row) in enumerate(excel_data.iterrows()):
                task = FillTask(
                    excel_row_idx=excel_idx,
                    web_row_idx=seq_idx,  # 使用从0开始的顺序索引
                    row_data=row.to_dict()
                )
                tasks.append(task)
                print(f"[AnchorResolver] Task: Excel行{excel_idx} → 网页输入框{seq_idx}")
        
        print(f"[AnchorResolver] 生成 {len(tasks)} 个填充任务 (锚点列: {anchor_column or '无'})")
        return FillQueue(tasks)
    
    def _scan_web_anchors(self, anchor_fingerprint) -> Dict[str, int]:
        """
        扫描网页中的锚点值
        
        Returns:
            {锚点值: 网页行索引}
        """
        web_anchor_map = {}
        
        if not self.tab:
            print("[AnchorResolver] ⚠️ 无浏览器 tab，无法扫描锚点")
            return web_anchor_map
        
        try:
            # 获取锚点列的 XPath 模板
            xpath = anchor_fingerprint.xpath if hasattr(anchor_fingerprint, 'xpath') else None
            if not xpath:
                return web_anchor_map
            
            # 获取关联元素列表
            related = getattr(anchor_fingerprint, 'related_inputs', [])
            all_xpaths = [xpath] + (related if related else [])
            
            for idx, xp in enumerate(all_xpaths):
                try:
                    ele = self.tab.ele(f'xpath:{xp}', timeout=0.1)
                    if ele:
                        # 获取文本内容（用于匹配）
                        text = ''
                        if hasattr(ele, 'text'):
                            text = ele.text.strip() if ele.text else ''
                        if not text and hasattr(ele, 'attr'):
                            text = ele.attr('value') or ''
                        
                        if text:
                            web_anchor_map[text] = idx
                except:
                    pass
            
            print(f"[AnchorResolver] 扫描到 {len(web_anchor_map)} 个网页锚点值")
            
        except Exception as e:
            print(f"[AnchorResolver] 扫描锚点失败: {e}")
        
        return web_anchor_map
