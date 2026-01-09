# RexTools3 Design Guide

## Overview
This document outlines the standard architecture, coding conventions, and UI patterns for the RexTools3 project. Following these guidelines ensures consistency and makes the codebase easier to navigate for both humans and LLMs.

## Directory Structure

| Path | Purpose |
| :--- | :--- |
| `core/` | Essential utilities (Theme, Notification, Config). |
| `ui/` | UI rendering engines and reusable widget helpers. |
| `operators/` | Blender Operators (Business Logic). |
| `panels/` | Blender UI Panels (Interface Definition). |
| `docs/` | Documentation (LLM Guides, User Manuals). |

## Naming Conventions
- **Classes**: PascalCase with prefix (e.g., `REXTOOLS3_OT_MyOperator`, `REXTOOLS3_PT_MyPanel`).
- **Files**: snake_case (e.g., `my_tool.py`).
- **Variables**: snake_case.
- **Constants**: UPPER_CASE (e.g., `DEFAULT_COLOR`).

## UI System

### 1. Colors & Theme
**Source of Truth**: `core/theme.py`
Never hardcode colors. always import `Theme`.

```python
from ..core.theme import Theme
color = Theme.COLOR_hIGHLIGHT
```

### 2. Notifications (The Overlay System)
**Module**: `core/notify.py`
Use this system to provide feedback to the user. Avoid using `self.report({'INFO'})` for important user-facing feedback unless it's a log message.

```python
from ..core import notify

notify.success("Operation Complete!")
notify.error("Something went wrong.")
```

### 3. Panel Development
**Module**: `ui/utils.py`
Standardize all panels using these helpers.

- **Grouping**: Always group related parameters.
  ```python
  from ..ui import utils
  col = utils.draw_section(layout, "Export Settings", icon='EXPORT')
  col.prop(...)
  ```

- **Inputs**: Use consistent buffering.
  ```python
  utils.draw_input_group(layout, "Name", obj, "name")
  ```

- **Buttons**:
  ```python
  utils.draw_call_to_action(layout, "my.op_id", "Run Tool")
  ```

## LLM Context
If you are an AI reading this:
1. **Check `core/theme.py`** first for style rules.
2. **Use `ui/utils.py`** for all new panels.
3. **Prefer `common` libraries** over duplicating code.
