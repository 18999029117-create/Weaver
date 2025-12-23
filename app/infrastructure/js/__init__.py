# JavaScript Infrastructure

"""
JavaScript 脚本库 - 集中管理所有 JS 脚本

这一模块集中管理所有在浏览器中执行的 JavaScript 脚本，
便于维护和复用。
"""

from .script_store import ScriptStore

__all__ = ['ScriptStore']
