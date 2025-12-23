"""
智能字段匹配器 - 自动匹配Excel列和网页字段

Type Hints:
- Excel列: List[str]
- 网页指纹: List[ElementFingerprint]
- 匹配结果: MatchResult TypedDict
"""
import re
from typing import List, Dict, Tuple, Optional, Set, TypedDict

# 避免循环导入
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.domain.entities import ElementFingerprint


class MatchResult(TypedDict):
    """匹配结果类型定义"""
    matched: List[Tuple[str, 'ElementFingerprint', int]]
    unmatched_excel: List[str]
    unmatched_web: List['ElementFingerprint']


class SmartMatcher:
    """
    智能字段匹配器
    
    使用多策略算法匹配 Excel 列名和网页元素指纹。
    
    匹配策略:
    1. 精确匹配 (100分)
    2. 包含关系 (80分)
    3. 拼音首字母 (60分)
    4. 分词重叠 (40-70分)
    """
    
    # 匹配阈值
    MATCH_THRESHOLD: int = 60
    
    @staticmethod
    def match_fields(
        excel_columns: List[str], 
        web_fingerprints: List['ElementFingerprint']
    ) -> MatchResult:
        """
        智能匹配Excel列和网页字段
        
        Args:
            excel_columns: Excel列名列表
            web_fingerprints: 网页元素指纹列表
            
        Returns:
            MatchResult: {
                'matched': [(excel_col, fingerprint, score), ...],
                'unmatched_excel': [excel_col, ...],
                'unmatched_web': [fingerprint, ...]
            }
        """
        print("\n=== 🎯 启动智能匹配 ===")
        
        matched: List[Tuple[str, 'ElementFingerprint', int]] = []
        unmatched_excel: List[str] = []
        used_fingerprints: Set[int] = set()
        
        for excel_col in excel_columns:
            best_match: Optional['ElementFingerprint'] = None
            best_score: int = 0
            
            for fingerprint in web_fingerprints:
                if id(fingerprint) in used_fingerprints:
                    continue
                
                # 计算匹配分数
                score = SmartMatcher._calculate_match_score(excel_col, fingerprint)
                
                if score > best_score:
                    best_score = score
                    best_match = fingerprint
            
            # 匹配阈值：60分以上认为匹配
            if best_score >= SmartMatcher.MATCH_THRESHOLD and best_match is not None:
                matched.append((excel_col, best_match, best_score))
                used_fingerprints.add(id(best_match))
                print(f"  ✅ [{excel_col}] ← {best_match.get_display_name()} (匹配度:{best_score}分)")
            else:
                unmatched_excel.append(excel_col)
                print(f"  ⚠️ [{excel_col}] 未找到匹配项 (最高分:{best_score})")
        
        # 未匹配的网页元素
        unmatched_web = [fp for fp in web_fingerprints if id(fp) not in used_fingerprints]
        
        print(f"\n匹配统计:")
        print(f"  成功匹配: {len(matched)}")
        print(f"  未匹配Excel列: {len(unmatched_excel)}")
        print(f"  未匹配网页元素: {len(unmatched_web)}")
        
        return {
            'matched': matched,
            'unmatched_excel': unmatched_excel,
            'unmatched_web': unmatched_web
        }
    
    @staticmethod
    def _calculate_match_score(excel_col: str, fingerprint: 'ElementFingerprint') -> int:
        """
        计算匹配分数（100分制）
        
        匹配策略：
        1. 完全相同 → 100分
        2. 包含关系 → 80分
        3. 拼音首字母相同 → 60分
        4. 部分关键词匹配 → 40-70分
        5. 无匹配 → 0分
        """
        score = 0
        
        # 规范化Excel列名
        excel_normalized = SmartMatcher._normalize_text(excel_col)
        
        # 获取网页元素的所有可能名称
        web_texts = []
        web_texts.append(fingerprint.anchors.get('label', ''))
        web_texts.append(fingerprint.features.get('name', ''))
        web_texts.append(fingerprint.anchors.get('placeholder', ''))
        web_texts.append(fingerprint.features.get('id', ''))
        
        # 规范化网页文本
        web_normalized = [SmartMatcher._normalize_text(t) for t in web_texts if t]
        
        # 策略1: 完全相同
        if excel_normalized in web_normalized:
            return 100
        
        # 策略2: 包含关系
        for web_text in web_normalized:
            if excel_normalized in web_text or web_text in excel_normalized:
                score = max(score, 80)
        
        # 策略3: 分词匹配
        excel_words = SmartMatcher._split_words(excel_col)
        for web_text_raw in web_texts:
            if not web_text_raw:
                continue
            web_words = SmartMatcher._split_words(web_text_raw)
            
            # 计算词重叠度
            common = set(excel_words) & set(web_words)
            if common:
                overlap = len(common) / max(len(excel_words), len(web_words))
                score = max(score, int(40 + overlap * 30))
        
        # 策略4: 拼音首字母匹配（简化版：英文缩写匹配）
        excel_initials = ''.join([w[0].lower() for w in excel_words if w])
        for web_text_raw in web_texts:
            if not web_text_raw:
                continue
            web_words = SmartMatcher._split_words(web_text_raw)
            web_initials = ''.join([w[0].lower() for w in web_words if w])
            
            if len(excel_initials) >= 2 and excel_initials == web_initials:
                score = max(score, 60)
        
        return score
    
    @staticmethod
    def _normalize_text(text: Optional[str]) -> str:
        """
        规范化文本（去除特殊字符、转小写）
        """
        if not text:
            return ''
        
        # 去除常见标点和空格
        text = re.sub(r'[：:：\s\-\_]+', '', text)
        return text.lower()
    
    @staticmethod
    def _split_words(text: Optional[str]) -> List[str]:
        """
        分词（支持中英文）
        """
        if not text:
            return []
        
        # 中文按字符分
        # 英文按空格、下划线、驼峰分
        words = []
        
        # 先按分隔符分
        parts = re.split(r'[\s\-\_]+', text)
        
        for part in parts:
            # 驼峰分词
            # userName → user Name
            camel_split = re.sub(r'([a-z])([A-Z])', r'\1 \2', part)
            words.extend(camel_split.split())
        
        return [w.lower() for w in words if w]
