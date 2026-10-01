# 832401311_calculator_backend

前后端分离计算器系统 —— **后端服务**。

负责接收计算请求、校验输入、解析数学表达式、完成计算、处理异常，并把计算历史持久化到数据库；通过 HTTP JSON API 供前端调用。

> 架构原则：**核心计算逻辑全部在后端完成**，前端不参与任何计算。

## 功能特性

- 基本四则运算：`+ - * /`
- 复合表达式：运算符优先级、括号、一元正负号（`-5`、`3 * -2`）、小数
- 异常处理：非法表达式、除零、缺括号等，返回明确的错误信息
- 计算历史：每次成功计算自动写入 SQLite 数据库
- 历史查询、按 ID 删除、清空全部
- 统一的 JSON 响应格式与合理的 HTTP 状态码
- 手写递归下降解析器，**不使用 `eval` / `exec`**

## 技术栈

| 类别 | 选择 |
|------|------|
| 语言 | Python 3.8+ |
| Web 服务 | 标准库 `http.server`（`ThreadingHTTPServer`） |
| 数据库 | SQLite（标准库 `sqlite3`） |
| 表达式解析 | 手写递归下降解析器 |

> 全部使用 Python 标准库，**零第三方依赖**，无需 `pip install`。

## 运行环境

- Python 3.8 及以上（3.12 实测通过）

## 目录结构

```
832401311_calculator_backend/
├── src/
│   ├── server.py        # 控制层：HTTP 路由 + 请求处理（controller）
│   ├── calculator.py    # 服务层：表达式解析与求值（service）
│   └── database.py      # 数据层：SQLite 持久化（model）
├── README.md
├── codestyle.md
└── .gitignore
```

## 安装与启动

无需安装第三方依赖，直接运行：

```bash
cd 832401311_calculator_backend
python src/server.py
```

启动后监听 `http://0.0.0.0:8000`，控制台会打印监听地址与数据库文件路径。

## 配置说明

通过环境变量配置（均可不设，使用默认值）：

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `PORT` | `8000` | 监听端口 |
| `HOST` | `0.0.0.0` | 监听地址 |
| `CALC_DB_PATH` | 项目根目录 `calculator.db` | SQLite 数据库文件路径 |

Windows PowerShell 示例：

```powershell
$env:PORT = "8080"
python src/server.py
```

## 数据库初始化

首次启动时自动建表，**无需手动初始化**。表结构：

```sql
CREATE TABLE calculation_history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    expression TEXT NOT NULL,
    result     TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

## API 接口

| 方法 | 路径 | 说明 | 成功状态码 |
|------|------|------|-----------|
| GET | `/api/health` | 健康检查 | 200 |
| POST | `/api/calculate` | 计算表达式 | 200 |
| GET | `/api/history` | 查询历史（按时间倒序） | 200 |
| DELETE | `/api/history/{id}` | 删除指定记录 | 200 |
| DELETE | `/api/history` | 清空全部历史（加分项） | 200 |

### 计算请求示例

```http
POST /api/calculate
Content-Type: application/json

{"expression": "(1+2)*3"}
```

成功响应：

```json
{"success": true, "expression": "(1+2)*3", "result": 9, "id": 1}
```

错误响应（非法表达式 / 除零，HTTP 400）：

```json
{"success": false, "message": "Division by zero"}
```

### 历史查询示例

```http
GET /api/history
```

```json
{
  "success": true,
  "history": [
    {"id": 2, "expression": "5*8", "result": "40", "created_at": "2026-10-01 10:21:00"},
    {"id": 1, "expression": "1+2", "result": "3",  "created_at": "2026-10-01 10:20:00"}
  ]
}
```

## 前后端连接方式

前端通过 `fetch` 调用上述 REST API。后端已开启 CORS（`Access-Control-Allow-Origin: *`），前端静态站点可直接跨域调用。前端只需把 `app.js` 顶部的 `API_BASE` 指向本服务的地址即可。

## 部署

### Render / Railway（推荐）

1. 新建 Web Service，选择 Python 环境。
2. Start Command 填：`python src/server.py`
3. 平台会自动注入 `PORT` 环境变量，服务监听 `0.0.0.0`，直接可用。
4. 数据文件 `calculator.db` 会写入实例磁盘（免费实例重启后可能重置，正式使用建议换成托管数据库）。

### PythonAnywhere

1. 上传代码，在 Web 标签页选择 WSGI 应用。
2. 用 Flask/自定义 WSGI 包装，或直接通过 Always-on task 运行 `python src/server.py` 并开放端口。

### 本地 / 服务器

```bash
python src/server.py
# 或指定端口
PORT=9000 python src/server.py
```

## 安全说明

- 表达式解析采用**手写递归下降解析器**，将输入作为纯数学处理，绝不执行用户输入为代码。
- 非法输入、除零、结果越界等均被捕获，返回 400 及明确错误信息，不泄露堆栈。

## 代码规范

见 [codestyle.md](./codestyle.md)，遵循 [PEP 8](https://peps.python.org/pep-0008/)。
