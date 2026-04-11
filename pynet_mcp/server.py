import asyncio
import json
import psutil
import ast
import threading
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("PyNet Platform Bridge")

PIPE_PREFIX = r'\\.\pipe\tool_runner_'

SUPPORTED_PRODUCTS = {
    "roamer.exe":  "Navisworks",
    "revit.exe":   "Revit",
    "acad.exe":    "AutoCAD",
}

ALLOWED_REFERENCES = {
    # Common .NET
    "System",
    "System.Windows.Forms",
    "System.Drawing",
    "System.Collections.Generic",
    # Navisworks
    "Autodesk.Navisworks.Api",
    "Autodesk.Navisworks.ComApi",
    "Autodesk.Navisworks.Interop.ComApi",
    "Autodesk.Navisworks.Clash",
    # Revit
    "RevitAPI",
    "RevitAPIUI",
    # AutoCAD / Civil 3D
    "AcMgd",
    "AcCoreMgd",
    "AcDbMgd",
    "AecBaseMgd",
    "AecPropDataMgd",
    "AeccDbMgd",
}

ALLOWED_REFERENCE_PREFIXES = (
    "Raen.Navisworks.Pynet.",
    "Raen.Revit.Pynet.",
    "Raen.Civil3D.Pynet.",
)

ALLOWED_PYTHON_IMPORTS = {
    "clr", "sys", "json", "re", "time", "datetime", "pathlib",
    "typing", "threading", "collections", "xml",
    "pandas", "plotly", "matplotlib", "dash", "webbrowser",
    "psutil",
}

BLOCKED_PYTHON_IMPORTS = {
    "os", "subprocess", "shutil", "socket", "ctypes", "pickle",
    "importlib", "http", "urllib", "signal", "multiprocessing",
    "tempfile", "glob", "inspect", "code", "codeop",
}

BLOCKED_CALLS = {
    "eval", "exec", "compile", "__import__",
    "getattr", "setattr", "delattr", "globals", "locals", "vars",
    "breakpoint",
}

ALLOWED_CLR_ROOTS = {ref.split(".")[0] for ref in ALLOWED_REFERENCES}


class ScriptAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.clr_references = []
        self.python_imports = []
        self.calls = []
        self.dangerous_attrs = []

    def visit_Import(self, node):
        for alias in node.names:
            root = alias.name.split(".")[0]
            self.python_imports.append(root)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            root = node.module.split(".")[0]
            self.python_imports.append(root)
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "AddReference":
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "clr":
                    if node.args and isinstance(node.args[0], ast.Constant):
                        self.clr_references.append(node.args[0].value)
            self.calls.append(node.func.attr)
        elif isinstance(node.func, ast.Name):
            self.calls.append(node.func.id)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if node.attr in ("__builtins__", "__subclasses__", "__globals__", "__code__"):
            self.dangerous_attrs.append(node.attr)
        self.generic_visit(node)

def check_references(refs):
    for ref in refs:
        if ref in ALLOWED_REFERENCES:
            continue
        if ref.startswith(ALLOWED_REFERENCE_PREFIXES):
            continue
        return False, f"Non-whitelisted assembly: {ref}"
    return True, None

def check_imports(imports):
    for imp in imports:
        if imp in BLOCKED_PYTHON_IMPORTS:
            return False, f"Blocked import: {imp}"
        if imp not in ALLOWED_PYTHON_IMPORTS and imp not in ALLOWED_CLR_ROOTS:
            return False, f"Non-whitelisted import: {imp}"
    return True, None

def check_calls(calls):
    for call in calls:
        if call in BLOCKED_CALLS:
            return False, f"Forbidden call: {call}"
    return True, None

def validate_script(script: str):
    try:
        tree = ast.parse(script)
    except SyntaxError as e:
        return False, f"Syntax error: {e}"

    analyzer = ScriptAnalyzer()
    analyzer.visit(tree)

    ok, msg = check_references(analyzer.clr_references)
    if not ok:
        return False, msg

    ok, msg = check_imports(analyzer.python_imports)
    if not ok:
        return False, msg

    ok, msg = check_calls(analyzer.calls)
    if not ok:
        return False, msg

    if analyzer.dangerous_attrs:
        return False, f"Dangerous attribute access: {analyzer.dangerous_attrs[0]}"

    return True, "OK"

def send_to_pipe(pid: int, payload: dict, timeout: float = 10.0) -> str:
    pipe_path = f"{PIPE_PREFIX}{pid}"
    result = [None]
    error = [None]

    def _open_and_communicate():
        try:
            pipe = open(pipe_path, 'r+b')
            message = json.dumps(payload).encode('utf-8') + b'\n'
            pipe.write(message)
            pipe.flush()
            response = pipe.readline()
            if response:
                result[0] = response.decode('utf-8').strip()
        except FileNotFoundError:
            error[0] = FileNotFoundError(f"PyNet Instance (PID {pid}) not found.")
        except Exception as e:
            error[0] = e

    worker = threading.Thread(target=_open_and_communicate, daemon=True)
    worker.start()
    worker.join(timeout=timeout)

    if worker.is_alive():
        return f"Timeout: No response from PID {pid} after {timeout}s."
    if error[0]:
        if isinstance(error[0], FileNotFoundError):
            return f"Error: {error[0]}"
        return f"IPC Error: {str(error[0])}"
    return result[0] or f"Success: Action {payload['Action']} executed on PID {pid}."


async def _send_with_heartbeat(pid: int, payload: dict, timeout: float, ctx: Context) -> str:
    pipe_path = f"{PIPE_PREFIX}{pid}"
    loop = asyncio.get_event_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def _communicate():
        try:
            pipe = open(pipe_path, 'r+b')
            pipe.write(json.dumps(payload).encode('utf-8') + b'\n')
            pipe.flush()
            while True:
                raw = pipe.readline()
                if not raw:
                    loop.call_soon_threadsafe(queue.put_nowait, (None, None))
                    break
                text = raw.decode('utf-8').strip()
                if not text:
                    continue
                try:
                    parsed = json.loads(text)
                except Exception:
                    parsed = {}
                loop.call_soon_threadsafe(queue.put_nowait, (text, parsed))
                if parsed.get("type") != "heartbeat":
                    break
        except FileNotFoundError:
            loop.call_soon_threadsafe(
                queue.put_nowait, (f"Error: PyNet Instance (PID {pid}) not found.", None)
            )
        except Exception as e:
            loop.call_soon_threadsafe(queue.put_nowait, (f"IPC Error: {e}", None))

    threading.Thread(target=_communicate, daemon=True).start()

    deadline = loop.time() + timeout
    while True:
        remaining = deadline - loop.time()
        if remaining <= 0:
            return f"Timeout: No response from PID {pid} after {timeout}s."
        try:
            text, parsed = await asyncio.wait_for(queue.get(), timeout=remaining)
        except asyncio.TimeoutError:
            return f"Timeout: No response from PID {pid} after {timeout}s."

        if text is None:
            return f"Error: Connection closed unexpectedly by PID {pid}."
        if parsed is None or parsed.get("type") != "heartbeat":
            return text

        beat = parsed.get("beat", "?")
        elapsed = parsed.get("elapsed", "?")
        await ctx.report_progress(beat, None, f"Executing script... {elapsed} elapsed")

@mcp.tool()
def list_active_instances() -> str:
    instances = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name = proc.info['name'].lower()
            product = SUPPORTED_PRODUCTS.get(name)
            if not product:
                continue
            pid = proc.info['pid']
            pipe_path = f"\\\\.\\pipe\\tool_runner_{pid}"
            try:
                with open(pipe_path, 'r+b'):
                    instances.append(f"{product} (PID {pid})")
            except OSError:
                continue
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return f"Active instances: {', '.join(instances)}" if instances else "No active instances found."

@mcp.tool()
def check_plugin_status(pid: int) -> str:
    payload = {
        "Action": "Ping",
        "Metadata": {"TargetPid": pid},
        "Content": ""
    }
    return send_to_pipe(pid, payload, timeout=5.0)

@mcp.tool()
async def send_command(pid: int, script_name: str, content: str, timeout: float, ctx: Context) -> str:
    valid, message = validate_script(content)

    if not valid:
        return f"Script rejected: {message}"

    payload = {
        "Action": "Execute",
        "Metadata": {
            "TargetPid": pid,
            "ScriptName": script_name
        },
        "Content": content
    }

    return await _send_with_heartbeat(pid, payload, timeout, ctx)

@mcp.tool()
def get_pynet_ui_layout(pid: int) -> str:
    payload = {
        "Action": "GetButtonsModules",
        "Metadata": {"TargetPid": pid},
        "Content": ""
    }
    return send_to_pipe(pid, payload, timeout=10.0)

@mcp.tool()
def create_pynet_module(pid: int, name: str) -> str:
    payload = {
        "Action": "CreateModule",
        "Metadata": {"TargetPid": pid},
        "Content": name
    }
    return send_to_pipe(pid, payload, timeout=10.0)

@mcp.tool()
def delete_pynet_module(pid: int, module_id: str) -> str:
    payload = {
        "Action": "DeleteModule",
        "Metadata": {
            "TargetPid": pid,
            "ModuleId": module_id
        },
        "Content": ""
    }
    return send_to_pipe(pid, payload, timeout=10.0)

def main():
    mcp.run()

if __name__ == "__main__":
    main()