# Quick Delete System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a configurable, multi-mode keyboard-driven Quick Delete system.

**Architecture:** Add a preference field `quick_delete_mode` to preferences. In the modal, load this setting and route both keyboard event handling and draw callbacks accordingly. Use three distinct paradigms (Nested, Grid, Modifier).

**Tech Stack:** Python, `bpy`, `bmesh`

---

### Task 1: Add quick_delete_mode to preferences

**Files:**
- Modify: `h:\Blender\RexTools3\preferences.py`

- [ ] **Step 1: Define quick_delete_mode EnumProperty**

Update `preferences.py` to add `quick_delete_mode` to `RexTools3Preferences` class (under `active_tab` or after line 346).

```python
    quick_delete_mode: EnumProperty(
        name="Quick Delete Mode",
        description="Paradigms for keyboard-driven quick delete system",
        items=[
            ('NESTED', "Nested WASD (Double-Tap)", "Two-step menu where WASD selects category first, then action", 'MENU_PANEL', 0),
            ('GRID', "Keyboard Grid Layout (Direct)", "Visual QWERTY layout grid for single-key actions", 'GRID', 1),
            ('MODIFIER', "Hold-and-Press Modifiers (WASD)", "Modifier keys (Shift/Alt/Ctrl) modify WASD actions", 'TRACKING', 2),
        ],
        default='NESTED',
    )
```

- [ ] **Step 2: Update Preferences UI draw method**

Modify the `draw()` method in `preferences.py` under the `SHORTCUTS` tab (around line 535) to display the new field when the modal is enabled.

Target change in `draw()` (lines 538-548 in original):
```python
            for enabled, toggle_prop_name, module, title in shortcut_tools:
                box = col.box()
                
                # Header row with enable/disable toggle
                hdr = box.row()
                hdr.prop(self, toggle_prop_name, text=title)
                
                if enabled and hasattr(module, 'addon_keymaps'):
                    if toggle_prop_name == "enable_quick_delete":
                        box.prop(self, "quick_delete_mode", text="Modal Mode")
                    keymap_col = box.column(align=True)
                    import rna_keymap_ui
                    for km, kmi in module.addon_keymaps:
                        keymap_col.context_pointer_set("keymap", km)
                        rna_keymap_ui.draw_kmi(None, kc, km, kmi, keymap_col, 0)
```

- [ ] **Step 3: Run validation to verify compilation and reload**

Run: `python .agent/scripts/reload_addon.py`
Expected: Reloads successfully without errors.

- [ ] **Step 4: Commit**

```bash
git add preferences.py
git commit -m "feat: add quick_delete_mode EnumProperty to preferences"
```

---

### Task 2: Implement key routing and state machine in quick_delete_modal.py

**Files:**
- Modify: `h:\Blender\RexTools3\operators\quick_delete_modal.py`

- [ ] **Step 1: Update Modal properties and initialization**

Modify `invoke` to fetch the preference mode and initialize category state.

```python
    def invoke(self, context, event):
        if context.space_data.type != 'VIEW_3D':
            self.report({'WARNING'}, "View3D not found")
            return {'CANCELLED'}

        # Get preference mode
        try:
            addon_name = ".".join(__package__.split(".")[:3]) if __package__ and __package__.startswith("bl_ext.") else (__package__.partition('.')[0] if __package__ else "RexTools3")
            prefs = context.preferences.addons[addon_name].preferences
            self.mode = prefs.quick_delete_mode
        except Exception:
            self.mode = 'NESTED'
            
        self.current_category = None
        self.shift_held = event.shift
        self.alt_held = event.alt
        self.ctrl_held = event.ctrl

        # Initialize UI at mouse position
        self.ui = ModalOverlay(title="Quick Delete", x=event.mouse_region_x, y=event.mouse_region_y)
        self.ui.visible = True
        
        # Add a callback to draw the HUD
        self._handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback, (context,), 'WINDOW', 'POST_PIXEL')
        
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
```

- [ ] **Step 2: Update modal event loop handling**

Modify `modal(self, context, event)` in `quick_delete_modal.py` to update shift/alt/ctrl state and properly handle backspace/escape in NESTED mode.

```python
    def modal(self, context, event):
        context.area.tag_redraw()
        self.shift_held = event.shift
        self.alt_held = event.alt
        self.ctrl_held = event.ctrl
        
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            if self.mode == 'NESTED' and self.current_category is not None and event.type == 'ESC':
                self.current_category = None
                return {'RUNNING_MODAL'}
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'X' and event.value == 'PRESS':
            self.cancel(context)
            return {'CANCELLED'}

        if event.value == 'PRESS':
            if self.mode == 'NESTED' and self.current_category is not None and event.type == 'BACKSPACE':
                self.current_category = None
                return {'RUNNING_MODAL'}
                
            result = self.handle_shortcuts(context, event)
            if result is not None:
                return result

        return {'RUNNING_MODAL'}
```

- [ ] **Step 3: Add shortcut handler routing method**

Add `handle_shortcuts`, `handle_nested_mode`, `handle_grid_mode`, and `handle_modifier_mode` to the class in `quick_delete_modal.py`.

```python
    def handle_shortcuts(self, context, event):
        if self.mode == 'NESTED':
            return self.handle_nested_mode(context, event)
        elif self.mode == 'GRID':
            return self.handle_grid_mode(context, event)
        elif self.mode == 'MODIFIER':
            return self.handle_modifier_mode(context, event)
        return None

    def handle_nested_mode(self, context, event):
        key = event.type
        if self.current_category is None:
            if key == 'A':
                self.current_category = 'DELETE'
            elif key == 'D':
                self.current_category = 'DISSOLVE'
            elif key == 'S':
                self.current_category = 'MERGE'
            elif key == 'W':
                self.current_category = 'EXTRAS'
            return None
        
        cat = self.current_category
        if cat == 'DELETE':
            if key == 'A':
                bpy.ops.mesh.delete(type='VERT')
            elif key == 'W':
                bpy.ops.mesh.delete(type='EDGE')
            elif key == 'D':
                bpy.ops.mesh.delete(type='FACE')
            elif key == 'S':
                bpy.ops.mesh.delete(type='EDGE_FACE')
            elif key == 'Q':
                bpy.ops.mesh.delete(type='ONLY_FACE')
            else:
                return None
            self.finish(context); return {'FINISHED'}
            
        elif cat == 'DISSOLVE':
            if key == 'A':
                bpy.ops.mesh.dissolve_verts()
            elif key == 'W':
                bpy.ops.mesh.dissolve_edges()
            elif key == 'D':
                bpy.ops.mesh.dissolve_faces()
            elif key == 'S':
                bpy.ops.mesh.edge_collapse()
            elif key == 'Q':
                bpy.ops.mesh.dissolve_limited()
            else:
                return None
            self.finish(context); return {'FINISHED'}
            
        elif cat == 'MERGE':
            if key == 'A':
                bpy.ops.mesh.merge(type='CENTER')
            elif key == 'W':
                bpy.ops.mesh.merge(type='CURSOR')
            elif key == 'D':
                bpy.ops.mesh.remove_doubles()
            elif key == 'S':
                bpy.ops.mesh.merge(type='COLLAPSE')
            else:
                return None
            self.finish(context); return {'FINISHED'}
            
        elif cat == 'EXTRAS':
            if key == 'A':
                bpy.ops.rextools3.delete_linked_ex()
            elif key == 'W':
                bpy.ops.mesh.checker_dissolve()
            elif key == 'D':
                bpy.ops.rextools3.loop_dissolve_ex()
            elif key == 'S':
                bpy.ops.rextools3.fill_loop_inner_region()
            else:
                return None
            self.finish(context); return {'FINISHED'}
            
        return None

    def handle_grid_mode(self, context, event):
        key = event.type
        if key == 'Q':
            bpy.ops.mesh.delete(type='VERT')
        elif key == 'W':
            bpy.ops.mesh.delete(type='EDGE')
        elif key == 'E':
            bpy.ops.mesh.delete(type='FACE')
        elif key == 'R':
            bpy.ops.rextools3.delete_linked_ex()
        elif key == 'A':
            bpy.ops.mesh.dissolve_verts()
        elif key == 'S':
            bpy.ops.mesh.dissolve_edges()
        elif key == 'D':
            bpy.ops.mesh.dissolve_faces()
        elif key == 'F':
            bpy.ops.mesh.checker_dissolve()
        elif key == 'Z':
            bpy.ops.mesh.merge(type='CENTER')
        elif key == 'X':
            bpy.ops.mesh.remove_doubles()
        elif key == 'C':
            bpy.ops.rextools3.loop_dissolve_ex()
        elif key == 'V':
            bpy.ops.rextools3.fill_loop_inner_region()
        else:
            return None
            
        self.finish(context); return {'FINISHED'}

    def handle_modifier_mode(self, context, event):
        key = event.type
        if event.shift:
            if key == 'A':
                bpy.ops.mesh.dissolve_verts()
            elif key == 'W':
                bpy.ops.mesh.dissolve_edges()
            elif key == 'D':
                bpy.ops.mesh.dissolve_faces()
            elif key == 'S':
                bpy.ops.mesh.dissolve_limited()
            else:
                return None
        elif event.alt:
            if key == 'A':
                bpy.ops.mesh.merge(type='CENTER')
            elif key == 'W':
                bpy.ops.mesh.merge(type='CURSOR')
            elif key == 'D':
                bpy.ops.mesh.remove_doubles()
            elif key == 'S':
                bpy.ops.mesh.merge(type='COLLAPSE')
            else:
                return None
        elif event.ctrl:
            if key == 'A':
                bpy.ops.rextools3.delete_linked_ex()
            elif key == 'W':
                bpy.ops.mesh.checker_dissolve()
            elif key == 'D':
                bpy.ops.rextools3.loop_dissolve_ex()
            elif key == 'S':
                bpy.ops.rextools3.fill_loop_inner_region()
            else:
                return None
        else:
            if key == 'A':
                bpy.ops.mesh.delete(type='VERT')
            elif key == 'W':
                bpy.ops.mesh.delete(type='EDGE')
            elif key == 'D':
                bpy.ops.mesh.delete(type='FACE')
            elif key == 'S':
                bpy.ops.mesh.delete(type='EDGE_FACE')
            else:
                return None
                
        self.finish(context); return {'FINISHED'}
```

- [ ] **Step 4: Run validation to verify compilation and reload**

Run: `python .agent/scripts/reload_addon.py`
Expected: Reloads successfully without errors.

- [ ] **Step 5: Commit**

```bash
git add operators/quick_delete_modal.py
git commit -m "feat: implement modal key routing handlers for Nested, Grid, and Modifier modes"
```

---

### Task 3: Update draw_callback HUD for each mode

**Files:**
- Modify: `h:\Blender\RexTools3\operators\quick_delete_modal.py`

- [ ] **Step 1: Replace draw_callback implementation**

Update `draw_callback(self, context)` to draw specialized content depending on `self.mode`.

```python
    def draw_callback(self, context):
        if not hasattr(self, 'ui'): return
        
        self.ui.items = []
        
        if self.mode == 'NESTED':
            if self.current_category is None:
                self.ui.title = "Quick Delete: Select Category"
                self.ui.add_value("Delete Options", "A", "➔")
                self.ui.add_value("Dissolve Options", "D", "➔")
                self.ui.add_value("Merge Options", "S", "➔")
                self.ui.add_value("Extras Options", "W", "➔")
            else:
                cat = self.current_category
                self.ui.title = f"Quick Delete: {cat.title()}"
                if cat == 'DELETE':
                    self.ui.add_value("Vertices", "A", "Delete")
                    self.ui.add_value("Edges", "W", "Delete")
                    self.ui.add_value("Faces", "D", "Delete")
                    self.ui.add_value("Only Edges & Faces", "S", "Delete")
                    self.ui.add_value("Only Faces", "Q", "Delete")
                elif cat == 'DISSOLVE':
                    self.ui.add_value("Vertices", "A", "Dissolve")
                    self.ui.add_value("Edges", "W", "Dissolve")
                    self.ui.add_value("Faces", "D", "Dissolve")
                    self.ui.add_value("Collapse Edges", "S", "Dissolve")
                    self.ui.add_value("Limited Dissolve", "Q", "Dissolve")
                elif cat == 'MERGE':
                    self.ui.add_value("Merge Center", "A", "Merge")
                    self.ui.add_value("Merge At Cursor", "W", "Merge")
                    self.ui.add_value("Merge By Distance", "D", "Merge")
                    self.ui.add_value("Merge Collapse", "S", "Merge")
                elif cat == 'EXTRAS':
                    self.ui.add_value("Delete Linked", "A", "Execute")
                    self.ui.add_value("Checker Dissolve", "W", "Execute")
                    self.ui.add_value("Loop Dissolve", "D", "Execute")
                    self.ui.add_value("Fill Loop Region", "S", "Execute")
                self.ui.add_value("Back to Main Menu", "Backspace/ESC", "")

        elif self.mode == 'GRID':
            self.ui.title = "Quick Delete: Direct Grid"
            self.ui.add_value("Delete: Vert / Edge / Face / Linked", "Q / W / E / R", "DELETE")
            self.ui.add_value("Dissolve: Vert / Edge / Face / Checker", "A / S / D / F", "DISSOLVE")
            self.ui.add_value("Merge: Center / By Dist", "Z / X", "MERGE")
            self.ui.add_value("Extras: Loop Dissolve / Fill Loop", "C / V", "EXTRAS")

        elif self.mode == 'MODIFIER':
            action_label = "DELETE"
            if self.shift_held:
                action_label = "DISSOLVE"
            elif self.alt_held:
                action_label = "MERGE"
            elif self.ctrl_held:
                action_label = "EXTRAS"
                
            self.ui.title = f"Quick {action_label.title()}"
            
            if not self.shift_held and not self.alt_held and not self.ctrl_held:
                self.ui.add_value("Vertices", "A", "Delete")
                self.ui.add_value("Edges", "W", "Delete")
                self.ui.add_value("Faces", "D", "Delete")
                self.ui.add_value("Only Edges/Faces", "S", "Delete")
            elif self.shift_held:
                self.ui.add_value("Vertices", "Shift+A", "Dissolve")
                self.ui.add_value("Edges", "Shift+W", "Dissolve")
                self.ui.add_value("Faces", "Shift+D", "Dissolve")
                self.ui.add_value("Limited Dissolve", "Shift+S", "Dissolve")
            elif self.alt_held:
                self.ui.add_value("Merge Center", "Alt+A", "Merge")
                self.ui.add_value("Merge At Cursor", "Alt+W", "Merge")
                self.ui.add_value("Merge By Distance", "Alt+D", "Merge")
                self.ui.add_value("Merge Collapse", "Alt+S", "Merge")
            elif self.ctrl_held:
                self.ui.add_value("Delete Linked", "Ctrl+A", "Execute")
                self.ui.add_value("Checker Dissolve", "Ctrl+W", "Execute")
                self.ui.add_value("Loop Dissolve", "Ctrl+D", "Execute")
                self.ui.add_value("Fill Loop Region", "Ctrl+S", "Execute")
                
            self.ui.add_value("Modifiers Guide", "Shift / Alt / Ctrl", "Switch Actions")

        self.ui.draw()
```

- [ ] **Step 2: Run validation to verify compilation and reload**

Run: `python .agent/scripts/reload_addon.py`
Expected: Reloads successfully without errors.

- [ ] **Step 3: Commit**

```bash
git add operators/quick_delete_modal.py
git commit -m "feat: implement HUD drawing callbacks for each mode"
```
