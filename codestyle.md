# 后端代码规范（codestyle）

> **规范来源**：本项目 Python 代码遵循 [PEP 8 — Style Guide for Python Code](https://peps.python.org/pep-0008/)，并结合 [Black](https://black.readthedocs.io/) 的常见约定。

## 1. 缩进

- 统一使用 **4 个空格**，禁止使用 Tab 键。

## 2. 行长

- 每行尽量不超过 **88 个字符**（PEP 8 建议 79，Black 等工具默认 88）。
- 过长的调用或表达式用括号换行。

## 3. 命名规范

| 对象 | 规范 | 示例 |
|------|------|------|
| 模块 / 函数 / 变量 | `snake_case` | `parse_expression`、`db_path` |
| 类 | `PascalCase` | `Database`、`CalculatorError` |
| 常量 | `UPPER_SNAKE_CASE` | `BASE_DIR`、`NUMBER` |
| 私有成员 | 单下划线前缀 | `self._conn` |

## 4. 空行

- 顶层函数与类之间空 **两行**。
- 类内方法之间空 **一行**。

## 5. 导入

- 每行一个 `import`；分组顺序：标准库 → 第三方 → 本地，组间空一行。
- 本项目只使用标准库。

## 6. 注释与 Docstring

- 模块、类、公开函数一律写 docstring（三引号）。
- 注释解释「为什么」，不重复「做什么」。
- 公开函数使用类型注解，例如 `def evaluate(expression: str) -> float:`。

## 7. 字符串与引号

- 统一使用双引号。
- 多行文本使用三引号。

## 8. 异常处理

- 自定义业务异常（本项目为 `CalculatorError`），统一在控制层捕获并转换为 HTTP 响应。
- 避免使用裸 `except:` 吞掉异常；确需兜底时明确注释原因。

## 9. 安全红线

- **禁止**使用 `eval`、`exec`、`compile` 等执行用户输入。
- 表达式解析必须走受控的解析器（本项目为递归下降解析器）。

## 10. 其他

- 使用 `from __future__ import annotations` 保持注解一致性。
- 保持函数职责单一：解析、持久化、路由分层清晰。
