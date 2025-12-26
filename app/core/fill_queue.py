"""
填充队列管理器

管理填充任务队列，支持单条/批量取任务，跟踪进度。
"""

from typing import List, Optional
from app.domain.entities.fill_task import FillTask


class FillQueue:
    """
    填充任务队列
    
    存储待填充任务列表，提供统一的任务获取接口。
    无论是单条录入还是批量录入，都通过此队列获取任务。
    
    - 单条录入: get_next(1) 获取 1 个任务
    - 批量录入: get_next(all) 获取全部任务
    """
    
    def __init__(self, tasks: List[FillTask] = None):
        self.tasks: List[FillTask] = tasks or []
        self._current_idx: int = 0
    
    def add_task(self, task: FillTask):
        """添加任务到队列"""
        self.tasks.append(task)
    
    def get_next(self, count: int = 1) -> List[FillTask]:
        """
        获取下一批待执行任务
        
        Args:
            count: 获取数量，-1 表示全部
            
        Returns:
            待执行任务列表
        """
        if count == -1:
            count = len(self.tasks)
        
        pending_tasks = []
        idx = self._current_idx
        
        while len(pending_tasks) < count and idx < len(self.tasks):
            task = self.tasks[idx]
            if task.is_pending:
                pending_tasks.append(task)
            idx += 1
        
        return pending_tasks
    
    def advance(self, count: int = 1):
        """前进指针（标记已处理）"""
        self._current_idx = min(self._current_idx + count, len(self.tasks))
    
    @property
    def current_index(self) -> int:
        """当前索引"""
        return self._current_idx
    
    @current_index.setter
    def current_index(self, value: int):
        """设置当前索引"""
        self._current_idx = max(0, min(value, len(self.tasks)))
    
    @property
    def total_count(self) -> int:
        """总任务数"""
        return len(self.tasks)
    
    @property
    def pending_count(self) -> int:
        """待处理任务数"""
        return sum(1 for t in self.tasks if t.is_pending)
    
    @property
    def success_count(self) -> int:
        """成功任务数"""
        return sum(1 for t in self.tasks if t.status == "success")
    
    @property
    def error_count(self) -> int:
        """失败任务数"""
        return sum(1 for t in self.tasks if t.status == "error")
    
    @property
    def has_more(self) -> bool:
        """是否还有待处理任务"""
        return self._current_idx < len(self.tasks)
    
    def reset(self):
        """重置队列进度"""
        self._current_idx = 0
        for task in self.tasks:
            task.status = "pending"
            task.error_message = None
