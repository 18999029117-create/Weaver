# Weaver 开发规范

> **版本**: 1.0  
> **最后更新**: 2024-12-23  
> **适用范围**: 所有贡献者

---

## 📋 目录

1. [项目结构](#项目结构)
2. [代码风格](#代码风格)
3. [命名规范](#命名规范)
4. [类型注解](#类型注解)
5. [文档规范](#文档规范)
6. [测试规范](#测试规范)
7. [Git 工作流](#git-工作流)
8. [代码审查](#代码审查)

---

## 项目结构

```
app/
├── ui/                  # 用户界面层
├── application/         # 应用层（编排器、控制器）
│   └── orchestrator/
│       └── strategies/  # 策略模式实现
├── core/                # 核心业务逻辑
│   ├── analyzer/        # 页面分析
│   └── filler/          # 表单填充
├── domain/              # 领域层（实体、值对象）
│   └── entities/
├── infrastructure/      # 基础设施层
│   └── js/              # JavaScript 脚本
├── utils/               # 工具类
├── config.py            # 集中配置
tests/
├── conftest.py          # pytest fixtures
└── unit/                # 单元测试
```

### 层级依赖原则

```
UI → Application → Core → Domain ← Infrastructure
```

- **禁止**: 下层依赖上层
- **禁止**: `core/` 导入 `ui/`
- **允许**: `ui/` 导入 `application/`

---

## 代码风格

### Python 版本
- **最低要求**: Python 3.9+
- **推荐**: Python 3.11

### 格式化工具
```bash
# 使用 ruff 格式化和检查
ruff check app/ --fix
ruff format app/
```

### 行长度
- **最大**: 100 字符
- **推荐**: 88 字符（Black 默认）

### 导入顺序
```python
# 1. 标准库
import os
import re
from typing import List, Dict, Optional

# 2. 第三方库
import pandas as pd
from DrissionPage import ChromiumPage

# 3. 本地模块
from app.domain.entities import ElementFingerprint
from app.core.smart_matcher import SmartMatcher
```

---

## 命名规范

### 文件命名
| 类型 | 规范 | 示例 |
|------|------|------|
| 模块 | `snake_case.py` | `smart_form_filler.py` |
| 测试 | `test_*.py` | `test_smart_matcher.py` |
| 策略类 | `*_strategy.py` | `anchor_fill_strategy.py` |

### 类命名
| 类型 | 规范 | 示例 |
|------|------|------|
| 普通类 | `PascalCase` | `SmartFormFiller` |
| 策略类 | `*Strategy` | `AnchorFillStrategy` |
| 适配器 | `*Adapter` | `ElementUIAdapter` |
| 控制器 | `*Controller` | `FillSessionController` |

### 方法命名
```python
# 公开方法: snake_case
def scan_page(self, timeout: float = 15.0) -> List[ElementFingerprint]:
    pass

# 私有方法: _开头
def _calculate_stability(self) -> int:
    pass

# 静态方法: 同公开方法
@staticmethod
def match_fields(columns: List[str]) -> dict:
    pass
```

### 常量命名
```python
# 模块级常量: UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 15.0

# 类常量
class SmartMatcher:
    MATCH_THRESHOLD: int = 60
```

---

## 类型注解

### 基本要求
- **所有公开方法**: 必须有类型注解
- **私有方法**: 推荐有类型注解
- **返回值**: 必须标注

### 示例
```python
from typing import List, Dict, Optional, Callable, Any

def match_fields(
    excel_columns: List[str],
    web_fingerprints: List[ElementFingerprint]
) -> Dict[str, Any]:
    """匹配 Excel 列和网页元素"""
    pass

def _fill_single_row(
    self,
    row_data: Any,
    row_index: int
) -> bool:
    """填充单行数据"""
    pass
```

### TypedDict 用于复杂返回值
```python
from typing import TypedDict, List, Tuple

class MatchResult(TypedDict):
    matched: List[Tuple[str, ElementFingerprint, int]]
    unmatched_excel: List[str]
    unmatched_web: List[ElementFingerprint]
```

### 避免循环导入
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.entities import ElementFingerprint
```

---

## 文档规范

### Docstring 格式（Google Style）
```python
def scan_page(self, max_wait: float = 15.0) -> List[ElementFingerprint]:
    """
    扫描网页元素
    
    使用 JS 快照模式深度扫描页面，提取所有可交互元素的指纹信息。
    
    Args:
        max_wait: 最大等待时间（秒），默认 15.0
        
    Returns:
        ElementFingerprint 列表
        
    Raises:
        TimeoutError: 页面加载超时
        
    Example:
        >>> fingerprints = controller.scan_page(timeout=10)
        >>> print(f"Found {len(fingerprints)} elements")
    """
    pass
```

### 模块级文档
```python
"""
智能表单填充器

提供带自愈机制的表单填充功能。

功能:
- 多选择器回退
- 自动元素重定位
- Vue/React 框架兼容

Usage:
    from app.core.smart_form_filler import SmartFormFiller
    
    result = SmartFormFiller.fill_form_with_healing(tab, data, mappings)
"""
```

---

## 测试规范

### 目录结构
```
tests/
├── conftest.py              # 共享 fixtures
├── unit/
│   ├── core/
│   │   └── test_smart_matcher.py
│   ├── domain/
│   │   └── test_element_fingerprint.py
│   └── utils/
│       └── test_logger.py
└── integration/             # 集成测试（未来）
```

### 测试命名
```python
class TestSmartMatcher:
    """SmartMatcher 测试套件"""
    
    def test_exact_match_returns_100_score(self):
        """精确匹配应返回 100 分"""
        pass
    
    def test_no_match_returns_zero_score(self):
        """无匹配应返回 0 分"""
        pass
```

### Fixture 使用
```python
# conftest.py
@pytest.fixture
def sample_element_data():
    """基础元素数据样本"""
    return {
        'id_selector': '#username',
        'xpath': '//input[@id="username"]',
        ...
    }

# test_*.py
def test_something(sample_element_data):
    fp = ElementFingerprint(sample_element_data)
    assert fp.stability_score > 0
```

### 运行测试
```bash
# 运行所有单元测试
python -m pytest tests/unit -v

# 运行特定测试
python -m pytest tests/unit/core/test_smart_matcher.py -v

# 带覆盖率
python -m pytest tests/unit --cov=app --cov-report=term-missing
```

---

## Git 工作流

### 分支命名
| 类型 | 格式 | 示例 |
|------|------|------|
| 功能 | `feature/<描述>` | `feature/add-pagination` |
| 修复 | `fix/<描述>` | `fix/iframe-detection` |
| 重构 | `refactor/<描述>` | `refactor/split-filler` |

### Commit 消息格式
```
<type>: <subject>

<body>
```

**Type 类型**:
- `feat`: 新功能
- `fix`: 修复 bug
- `refactor`: 重构（不改变功能）
- `docs`: 文档更新
- `test`: 添加测试
- `chore`: 构建/配置变更

**示例**:
```
feat: add anchor-based row matching

- Implement AnchorFillStrategy
- Support multi-page fill with pagination
- Add key column configuration
```

### PR 检查清单
- [ ] 代码通过 `ruff check`
- [ ] 类型检查通过 `mypy`
- [ ] 所有测试通过
- [ ] 新功能有对应测试
- [ ] 文档已更新

---

## 代码审查

### 审查重点
1. **功能正确性**: 是否实现需求
2. **代码风格**: 是否符合规范
3. **测试覆盖**: 是否有足够测试
4. **性能影响**: 是否影响页面加载
5. **向后兼容**: 是否破坏现有功能

### 禁止事项
- ❌ 在 `core/` 层使用 `print()`（使用 `logger`）
- ❌ 硬编码超时值（使用 `app.config`）
- ❌ 直接捕获 `Exception` 不处理
- ❌ 提交 `__pycache__` 或 `.pyc` 文件
- ❌ 在主分支直接提交

### 推荐做法
- ✅ 使用类型注解
- ✅ 编写单元测试
- ✅ 使用配置模块
- ✅ 遵循策略模式扩展功能
- ✅ 保持函数小而专注

---

## 快速参考

### 常用命令
```bash
# 运行应用
python main.py

# 运行测试
python -m pytest tests/unit -v

# 代码检查
ruff check app/

# 类型检查
mypy app/ --ignore-missing-imports

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 配置使用
```python
from app.config import scanner_config, matcher_config

timeout = scanner_config.max_wait
threshold = matcher_config.min_score_threshold
```

### 日志使用
```python
from app.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("操作完成")
logger.success("填充成功")
logger.error("发生错误")
```

---

**维护者**: Weaver Team  
**问题反馈**: [GitHub Issues](https://github.com/18999029117-create/Weaver/issues)
