"""计算器后端的 HTTP API 服务（控制层 / 入口）。

基于标准库 :class:`http.server.ThreadingHTTPServer`，无需任何 Web 框架。
这里的职责只有：路由、解析请求体、调用计算服务与数据库、返回标准化的
JSON 响应。

接口一览
---------
GET    /api/health          健康检查          -> {"status": "ok"}
POST   /api/calculate       计算表达式        -> 计算结果
GET    /api/history         查询历史          -> 历史记录列表
DELETE /api/history/{id}    删除指定记录      -> 删除结果
DELETE /api/history         清空全部历史（加分项）
"""

from __future__ import annotations

import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import calculator
import database

# 项目根目录（backend 目录），数据库文件默认放在这里。
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get("CALC_DB_PATH", os.path.join(BASE_DIR, "calculator.db"))

db = database.Database(DB_PATH)

HISTORY_RE = re.compile(r"^/api/history/(\d+)$")


def _add_cors(handler: BaseHTTPRequestHandler) -> None:
    """添加跨域响应头，允许前端静态站点跨域调用。"""
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")


def _send_json(handler: BaseHTTPRequestHandler, status: int, payload) -> None:
    """以统一格式返回 JSON 响应。"""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    _add_cors(handler)
    handler.end_headers()
    handler.wfile.write(body)


class CalculatorHandler(BaseHTTPRequestHandler):
    server_version = "CalculatorBackend/1.0"

    def log_message(self, format, *args):  # noqa: A002
        # 保持控制台输出简洁。
        print("%s %s" % (self.address_string(), format % args))

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError("Invalid JSON body") from exc
        if not isinstance(data, dict):
            raise ValueError("Request body must be a JSON object")
        return data

    # ---- 路由分发 -------------------------------------------------------

    def do_OPTIONS(self) -> None:
        # 浏览器跨域预检请求。
        self.send_response(204)
        _add_cors(self)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            _send_json(self, 200, {"status": "ok"})
            return
        if path == "/api/history":
            _send_json(self, 200, {"success": True, "history": db.list_all()})
            return
        _send_json(self, 404, {"success": False, "message": "Not found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/api/calculate":
            _send_json(self, 404, {"success": False, "message": "Not found"})
            return
        try:
            body = self._read_json()
        except ValueError as exc:
            _send_json(self, 400, {"success": False, "message": str(exc)})
            return

        expression = body.get("expression")
        if not isinstance(expression, str) or not expression.strip():
            _send_json(
                self, 400,
                {"success": False, "message": "Expression is required"},
            )
            return
        expression = expression.strip()

        try:
            value = calculator.evaluate(expression)
        except calculator.CalculatorError as exc:
            _send_json(self, 400, {"success": False, "message": str(exc)})
            return
        except Exception:  # 防御性兜底：绝不让堆栈泄露给客户端。
            _send_json(
                self, 500,
                {"success": False, "message": "Internal calculation error"},
            )
            return

        display = calculator.format_result(value)
        record_id = db.insert(expression, display)
        _send_json(
            self,
            200,
            {
                "success": True,
                "expression": expression,
                "result": calculator.to_json_number(value),
                "id": record_id,
            },
        )

    def do_DELETE(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/history":
            count = db.clear()
            _send_json(self, 200, {"success": True, "deleted": count})
            return
        match = HISTORY_RE.match(path)
        if match:
            record_id = int(match.group(1))
            deleted = db.delete(record_id)
            if deleted == 0:
                _send_json(
                    self, 404,
                    {"success": False, "message": "Record not found"},
                )
            else:
                _send_json(self, 200, {"success": True, "deleted": deleted})
            return
        _send_json(self, 404, {"success": False, "message": "Not found"})


def main() -> None:
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), CalculatorHandler)
    print("Calculator backend listening on http://%s:%d" % (host, port))
    print("Database file: %s" % DB_PATH)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        server.server_close()
        db.close()


if __name__ == "__main__":
    main()
