"""
元素指纹模块 - 兼容层

此文件保持向后兼容，实际实现已移至 domain.entities.element_fingerprint

注意: 新代码应直接从 app.domain.entities 导入
"""

# 向后兼容导入
from app.domain.entities.element_fingerprint import ElementFingerprint

__all__ = ['ElementFingerprint']
