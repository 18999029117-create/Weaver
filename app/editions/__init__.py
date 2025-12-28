"""
版本系统模块

提供定制化版本选择和管理功能。
"""

from app.editions.registry import EDITIONS, get_edition, get_edition_names
from app.editions.base_edition import BaseEdition

__all__ = ['EDITIONS', 'get_edition', 'get_edition_names', 'BaseEdition']
