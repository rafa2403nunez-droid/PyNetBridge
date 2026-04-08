<p align="center">
  <img src="https://github.com/rafa2403nunez-droid/PyNetBridge/blob/main/Assets/PyNetBridge.png" width="300"/>
</p>


# 🐍 PyNet Platform Bridge (MCP)

**PyNet Platform Bridge (MCP)** is the execution layer that allows AI models to control Autodesk tools in real-time.

It connects Natural Language → Python → Navisworks (Revit & Civil 3D coming soon), enabling AI to generate, execute, and refine BIM workflows autonomously.

Available Integration includes **Navisworks Manage**. Revit and Civil 3D **coming soon**.

This bridge acts as the connective tissue between AI logic and Autodesk desktop APIs, allowing for dynamic UI creation, script execution, and BIM process automation using natural language.

## 🔄 How it works

1. The user describes a task in natural language.  
2. The AI generates a Python script.
3. PyNet Bridge validates and sends the script.
4. The PyNet plugin executes it inside Autodesk.
5. Results are returned back to the AI.

This is what turns AI from a chatbot into an execution engine for BIM.

---

## 🚀 What makes PyNet Bridge powerful

* **AI → Action:** Turns AI-generated code into real actions inside Navisworks/Revit  
* **Real-time Execution:** Run scripts instantly without leaving the BIM environment  
* **Dynamic UI Creation:** Let AI create tools, buttons and workflows on the fly  
* **Reliable Communication:** Fast and stable IPC using Named Pipes  
* **Model-Aware Automation:** Operates directly on live BIM models  

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

These tools allow AI to fully control the PyNet environment, from UI creation to script execution and system monitoring.
Once connected, the AI will have access to the full suite of PyNet tools:

### 🧠 Core capabilities exposed to AI

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

## 🛡️ Safe AI Execution

PyNet Bridge includes a built-in validation layer that ensures all AI-generated scripts are safe and controlled before execution.

✔ Prevents unsafe operations  
✔ Blocks unauthorized system access  
✔ Guarantees controlled interaction with BIM models  

**AI remains powerful**, but within safe boundaries

Starting from **v1.1.1**, the MCP server includes a built-in static analyzer that validates every script before it reaches Navisworks. All scripts are parsed and inspected at the bridge level — **rejected scripts never leave the MCP server**.

### Allowed CLR Assemblies
Only these .NET references are permitted via `clr.AddReference`:
- `Autodesk.Navisworks.Api`, `.ComApi`, `.Interop.ComApi`, `.Clash`
- `System`, `System.Windows.Forms`, `System.Drawing`, `System.Collections.Generic`
- `Raen.Navisworks.Pynet.2024`

### Allowed Python Imports
`clr`, `sys`, `json`, `re`, `time`, `datetime`, `pathlib`, `typing`, `threading`, `collections`, `xml`, `pandas`, `plotly`, `matplotlib`, `dash`, `webbrowser`, `psutil`

### Blocked Python Imports
`os`, `subprocess`, `shutil`, `socket`, `ctypes`, `pickle`, `importlib`, `http`, `urllib`, `signal`, `multiprocessing`, `tempfile`, `glob`, `inspect`, `code`, `codeop`

### Blocked Calls
`eval`, `exec`, `compile`, `__import__`, `getattr`, `setattr`, `delattr`, `globals`, `locals`, `vars`, `breakpoint`, `open`

### Blocked Attribute Access
`__builtins__`, `__subclasses__`, `__globals__`, `__code__`

> Any script that violates these rules is immediately rejected with a descriptive error message, without ever being sent to the plugin.

---

## 📂 Project Structure

* **pynet_mcp/**: Core MCP server logic (FastMCP).
* **pyproject.toml**: Package configuration and dependency management.

---

## 📥 Getting Started

Start building autonomous BIM workflows in minutes.

Install the bridge, connect your AI client, and turn natural language into real actions inside your models.

---

## 📄 License

This project is licensed under the MIT License.

---
<p align="center">
  Developed by <b>RAEN Digital Tools</b>
  <br/><br/>
  <img src="https://github.com/rafa2403nunez-droid/PyNetBridge/blob/main/Assets/RAENDigitalTools.png" alt="RAEN Digital Tools" width="200">
</p>
