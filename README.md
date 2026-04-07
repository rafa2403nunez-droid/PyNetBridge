<p align="center">
  <img src="https://github.com/rafa2403nunez-droid/PyNetBridge/blob/main/Assets/PyNetBridge.png" width="300"/>
</p>


# 🐍 PyNet Platform Bridge (MCP)

**PyNet Platform Bridge** is a Model Context Protocol (MCP) server that enables AI models (such as Claude, GPT-4o, or Gemini) to interact directly with **Autodesk Tools** through the PyNet Platform.

This bridge acts as the connective tissue between AI logic and Autodesk desktop APIs, allowing for dynamic UI creation, script execution, and BIM process automation using natural language.

---

## 🚀 Key Features

* **Dynamic UI Deployment:** Allows the AI to create custom Ribbon tabs (modules) and buttons in Navisworks/Revit in real-time.
* **Script Execution:** Seamlessly send and execute Python code directly within the PyNet Platform's internal engine.
* **Instance Detection:** Automatically locates active Navisworks/Revit processes using PID tracking via psutil.
* **Robust Communication:** Built on Named Pipes for low-latency, high-reliability IPC (Inter-Process Communication).
* **Open Ecosystem:** Compatible with any MCP client (Claude Desktop, Cursor, VS Code, Zed, etc.).

---

## 🛠️ Installation

### ✅ Option A — Automatic installer (recommended)

Open PowerShell and run:

```powershell
irm https://raw.githubusercontent.com/rafa2403nunez-droid/PyNetBridge/main/install.ps1 | iex
```

This will automatically:
1. Install `pynet-mcp-bridge` from PyPI
2. Configure **Claude Desktop** (supports both standard and Microsoft Store versions)
3. Configure **Claude Code** (VS Code extension)

> Restart Claude Desktop and/or VS Code after installation.

### Prerequisites
* **PyNet Platform** plugin installed in Navisworks/Revit.
* Python 3.10 or higher → [python.org](https://www.python.org/downloads/)

---

### 🔧 Option B — Manual installation

**1. Install the package:**

```bash
pip install pynet-mcp-bridge
```

**2. Configure Claude Desktop:**

Add the following to your `claude_desktop_config.json`:
- Standard: `%APPDATA%\Claude\claude_desktop_config.json`
- Microsoft Store: `%LOCALAPPDATA%\Packages\Claude_*\LocalCache\Roaming\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "pynet-bridge": {
      "command": "pynet-bridge",
      "args": []
    }
  }
}
```

**3. Configure Claude Code (VS Code extension):**

Add to `%USERPROFILE%\.claude.json`:

```json
{
  "mcpServers": {
    "pynet-bridge": {
      "type": "stdio",
      "command": "pynet-bridge",
      "args": []
    }
  }
}
```

---

## 🛠️ Available MCP Tools

Once connected, the AI will have access to the full suite of PyNet tools:

### 🔍 System & Connection
* **list_active_instances**: Scans the system for running Navisworks processes (`roamer.exe`) with an active PyNet IPC pipe.
* **check_plugin_status**: Handshake ping to verify the plugin listener is responsive.

### 🏗️ Module (Tab) Management
* **get_pynet_ui_layout**: Fetches the full UI structure (ButtonsModules and ScriptButtons).
* **create_pynet_module**: Creates a new custom Tab (ButtonsModule) in the Ribbon.
* **delete_pynet_module**: Permanently deletes a module and all its contents.

### 🔘 Button Management
* **get_buttons_data**: Lists all script buttons for a specific module ID.
* **deploy_script_button**: Installs a new ScriptButton into a specific module (Name, Script, Icon, Tooltip).
* **update_script_button**: Updates metadata for an existing ScriptButton or moves it to another module.
* **delete_script_button**: Permanently removes a ScriptButton from a module by Id.

### 💻 Execution & Console Control
* **send_command**: Direct script execution in the PyNet engine (Target PID, Script Name, Content).
* **get_output_window_status**: Checks if the output window is currently available/visible.
* **configure_output_window**: Toggles the visibility of the PyNet log/output window.

---

## 📂 Project Structure

* **pynet_mcp/**: Core MCP server logic (FastMCP).
* **pyproject.toml**: Package configuration and dependency management.

---

## 📄 License

This project is licensed under the MIT License.

---
<p align="center">
  Developed by <b>RAEN Digital Tools</b>
  <br/><br/>
  <img src="https://github.com/rafa2403nunez-droid/PyNetBridge/blob/main/Assets/RAENDigitalTools.png" alt="RAEN Digital Tools" width="200">
</p>
