import json
import psutil
import ast
import threading
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("PyNet Platform Bridge")

PIPE_PREFIX = r'\\.\pipe\tool_runner_'
TARGET_PROCESS = "roamer.exe"

ALLOWED_REFERENCES = {
    "Autodesk.Navisworks.Api",
    "Autodesk.Navisworks.ComApi",
    "Autodesk.Navisworks.Interop.ComApi",
    "Autodesk.Navisworks.Clash",
    "System",
    "System.Windows.Forms",
    "System.Drawing",
    "System.Collections.Generic",
    "Raen.Navisworks.Pynet.2024",
}

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
    "breakpoint", "open",
}


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
        if ref not in ALLOWED_REFERENCES:
            return False, f"Non-whitelisted assembly: {ref}"
    return True, None

def check_imports(imports):
    for imp in imports:
        if imp in BLOCKED_PYTHON_IMPORTS:
            return False, f"Blocked import: {imp}"
        if imp not in ALLOWED_PYTHON_IMPORTS:
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

    def _read(pipe):
        try:
            response = pipe.readline()
            if response:
                result[0] = response.decode('utf-8').strip()
        except Exception as e:
            error[0] = e

    try:
        with open(pipe_path, 'r+b') as pipe:
            message = json.dumps(payload).encode('utf-8') + b'\n'
            pipe.write(message)
            pipe.flush()

            reader = threading.Thread(target=_read, args=(pipe,), daemon=True)
            reader.start()
            reader.join(timeout=timeout)

            if reader.is_alive():
                return f"Timeout: No response from PID {pid} after {timeout}s."
            if error[0]:
                return f"IPC Error: {str(error[0])}"
            return result[0] or f"Success: Action {payload['Action']} executed on PID {pid}."

    except FileNotFoundError:
        return f"Error: PyNet Instance (PID {pid}) not found."
    except Exception as e:
        return f"IPC Error: {str(e)}"

@mcp.tool()
def list_active_instances() -> str:
    pids = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'].lower() == TARGET_PROCESS:
                pid = proc.info['pid']
                pipe_path = f"\\\\.\\pipe\\tool_runner_{pid}"
                try:
                    with open(pipe_path, 'r+b'):
                        pids.append(pid)
                except OSError:
                    continue
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return f"Active PIDs: {', '.join(map(str, pids))}" if pids else "No active instances found."

@mcp.tool()
def check_plugin_status(pid: int) -> str:
    payload = {
        "Action": "Ping",
        "Metadata": {"TargetPid": pid},
        "Content": ""
    }
    return send_to_pipe(pid, payload, timeout=5.0)

@mcp.tool()
def send_command(pid: int, script_name: str, content: str, timeout: float = 60.0) -> str:
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

    return send_to_pipe(pid, payload, timeout=timeout)

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