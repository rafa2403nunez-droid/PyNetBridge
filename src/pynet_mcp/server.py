import json
import psutil
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("PyNet Platform Bridge")
PIPE_PREFIX = r'\\.\pipe\tool_runner_'
TARGET_PROCESS = "roamer.exe"

def send_to_pipe(pid: int, payload: dict) -> str:
    """
    Universal dispatcher optimized for PyNet Platform classes.
    Matches the C# mcpActions enum names.
    """
    pipe_path = f"{PIPE_PREFIX}{pid}"
    try:
        with open(pipe_path, 'r+b') as pipe:
            message = json.dumps(payload).encode('utf-8') + b'\n'
            pipe.write(message)
            pipe.flush()

            response = pipe.readline()
            if response:
                return response.decode('utf-8').strip()
            return f"Success: Action {payload['Action']} executed on PID {pid}."
            
    except FileNotFoundError:
        return f"Error: PyNet Instance (PID {pid}) not found."
    except Exception as e:
        return f"IPC Error: {str(e)}"

@mcp.tool()
def list_active_instances() -> str:
    """Retrieves PIDs for all Navisworks instances with an active PyNet listener."""
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
    """Handshake ping to verify the plugin listener is responsive."""
    payload = {
        "Action": "Ping",
        "Metadata": {"TargetPid": pid},
        "Content": ""
    }
    return send_to_pipe(pid, payload)

@mcp.tool()
def send_command(pid: int, script_name: str, content: str) -> str:
    """Direct script execution in the PyNet engine."""
    payload = {
        "Action": "Execute",
        "Metadata": {
            "TargetPid": pid,
            "ScriptName": script_name
        },
        "Content": content
    }
    return send_to_pipe(pid, payload)


@mcp.tool()
def get_pynet_ui_layout(pid: int) -> str:
    """Fetches the full UI structure (ButtonsModules and ScriptButtons)."""
    payload = {
        "Action": "GetButtonsModules",
        "Metadata": {"TargetPid": pid},
        "Content": ""
    }
    return send_to_pipe(pid, payload)

@mcp.tool()
def get_buttons_data(pid: int, module_id: str) -> str:
    """Lists all script buttons for a specific module ID."""
    payload = {
        "Action": "GetButtonsData",
        "Metadata": {
            "TargetPid": pid,
            "ModuleId": module_id
        },
        "Content": ""
    }
    return send_to_pipe(pid, payload)

@mcp.tool()
def get_output_window_status(pid: int) -> str:
    """Get if the output window is available or not."""
    payload = {
        "Action": "GetOutputWindowStatus",
        "Metadata": {
            "TargetPid": pid,
        },
        "Content": ""
    }
    return send_to_pipe(pid, payload)

@mcp.tool()
def create_pynet_module(pid: int, name: str) -> str:
    """Creates a new ButtonsModule."""
    payload = {
        "Action": "CreateModule",
        "Metadata": {"TargetPid": pid},
        "Content": name 
    }
    return send_to_pipe(pid, payload)

@mcp.tool()
def delete_pynet_module(pid: int, module_id: str) -> str:
    """Permanently deletes a module."""
    payload = {
        "Action": "DeleteModule", # Matches mcpActions.DeleteModule
        "Metadata": {
            "TargetPid": pid,
            "ModuleId": module_id
        },
        "Content": ""
    }
    return send_to_pipe(pid, payload)

@mcp.tool()
def deploy_script_button(
    pid: int, 
    module_id: str, 
    name: str, 
    script_Path: str, 
    icon_name: str = "Default", 
    tooltip: str = ""
) -> str:
    """Installs a ScriptButton into a specific ButtonsModule."""
    button_data = {
        "Name": name,
        "ScriptPath": script_Path,
        "IconName": icon_name,
        "Tooltip": tooltip
    }
    
    payload = {
        "Action": "CreateButtonData",
        "Metadata": {
            "TargetPid": pid,
            "ModuleId": module_id
        },
        "Content": json.dumps(button_data)
    }
    return send_to_pipe(pid, payload)

@mcp.tool()
def update_script_button(
    pid: int,
    module_id: str,
    button_id: str,
    name: str,
    script_Path: str,
    icon_name: str,
    tooltip: str,
    dest_module_id: str = None
) -> str:
    """Updates metadata for an existing ScriptButton."""
    button_data = {
        "Id": button_id,
        "Name": name,
        "ScriptPath": script_Path,
        "IconName": icon_name,
        "Tooltip": tooltip
    }

    payload = {
        "Action": "UpdateButtonData",
        "Metadata": {
            "TargetPid": pid,
            "ModuleId": module_id,
            "ButtonId": button_id,
            "DestModuleId": dest_module_id if dest_module_id else module_id
        },
        "Content": json.dumps(button_data)
    }
    return send_to_pipe(pid, payload)

@mcp.tool()
def delete_script_button(pid: int, module_id: str, button_id: str) -> str:
    """Permanently removes a ScriptButton from a module by Id."""
    payload = {
        "Action": "DeleteButtonData",
        "Metadata": {
            "TargetPid": pid,
            "ModuleId": module_id,
            "ButtonId": button_id
        },
        "Content": ""
    }
    return send_to_pipe(pid, payload)

@mcp.tool()
def configure_output_window(pid: int, is_available: bool) -> str:
    """Toggles the visibility of the PyNet log/output window."""
    payload = {
        "Action": "ConfigureOutputWindow",
        "Metadata": {"TargetPid": pid},
        "Content": str(is_available).lower()
    }
    return send_to_pipe(pid, payload)