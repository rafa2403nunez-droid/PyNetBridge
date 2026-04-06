# 🏗️ PyNet Platform Bridge (MCP)

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

### 1. Prerequisites
* **PyNet Platform** plugin installed in Navisworks/Revit.
* Python 3.10 or higher.

### 2. Install the Bridge
Run the following command in your terminal:

pip install .

This will register the **pynet-bridge** command globally in your system.

---

## ⚙️ Configuration for Claude Desktop

To allow Claude to control your BIM environment, add the server to your Claude Desktop configuration file.

**File Path:** %APPDATA%\Claude\claude_desktop_config.json

**Configuration JSON:**

```json
{
  "mcpServers": {
    "pynet-platform": {
      "command": "pynet-bridge",
      "args": [],
      "env": {
        "PYTHONPATH": "path/to/your/src" 
      }
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

* **src/pynet_mcp/**: Core MCP server logic (FastMCP).
* **pyproject.toml**: Package configuration and dependency management.
* **Connectors/**: C# Plugins for Navisworks/Revit (Core integration).

---

## 📄 License

This project is licensed under the MIT License.

---
Built with ❤️ for the BIM Community by [rafa2403nunez](https://github.com/rafa2403nunez-droid)

<p align="center">
  <img src="https://raw.githubusercontent.com/rafa2403nunez-droid/PyNetBridge/develop/Assets/RAEN%20Digital%20Tools.png" alt="RAEN Digital Tools" width="200">
</p>
