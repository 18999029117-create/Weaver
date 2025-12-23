# Domain Interfaces

"""
领域接口 - 抽象契约定义

使用 Python Protocol (Structural Subtyping) 定义接口，
实现依赖反转原则 (DIP)。
"""

from .analyzer import IFormAnalyzer
from .filler import IFormFiller
from .browser import IBrowserAdapter

__all__ = [
    'IFormAnalyzer',
    'IFormFiller', 
    'IBrowserAdapter',
]
