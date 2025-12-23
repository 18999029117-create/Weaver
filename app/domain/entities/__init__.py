# Domain Entities

"""
领域实体 - 核心业务对象

提供应用程序的核心数据模型，不依赖任何外部框架。
"""

from .element_fingerprint import ElementFingerprint
from .fill_models import FillRecord, FillProgress, PageState

__all__ = [
    'ElementFingerprint',
    'FillRecord',
    'FillProgress',
    'PageState',
]
