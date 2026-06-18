# Design Specification: Keyboard-Driven Quick Delete System

This document outlines the design for implementing a highly configurable, keyboard-driven Quick Delete system for the RexTools3 Blender add-on. It allows the user to perform delete, dissolve, merge, and extra loop operations quickly in Edit Mode without relying on the mouse.

---

## Goal

To provide three distinct keyboard-navigation paradigms inside a custom modal, switchable via the Add-on Preferences, catering to different muscle-memory and workflow preferences.

---

## User Review Required

No breaking changes are introduced. The existing quick delete modal (`rextools3.quick_delete_modal`) will be updated to load the preferred workflow mode from Add-on Preferences and display/behave accordingly.

---

## Architectural Changes

### 1. Preferences Addition
*   **Target File:** [preferences.py](file:///h:/Blender/RexTools3/preferences.py)
*   **Property:** `quick_delete_mode` (`EnumProperty`)
    *   `'NESTED'`: Nested WASD Categories (Double-Tap)
    *   `'GRID'`: Keyboard Grid Layout (Direct)
    *   `'MODIFIER'`: Hold-and-Press Modifiers (WASD)
*   **Default:** `'NESTED'`
*   **UI:** Displayed under the `SHORTCUTS` tab in the addon preferences, right next to the "Quick Delete Modal" keymap configurations.

### 2. Modal Behavior & HUD Update
*   **Target File:** [quick_delete_modal.py](file:///h:/Blender/RexTools3/operators/quick_delete_modal.py)
*   **Logic:**
    *   Read `quick_delete_mode` from the addon preferences on invocation and on modal event loops.
    *   Adapt key event interception based on the active mode.
    *   Adapt `draw_callback` to draw HUD elements corresponding to the layout of the active mode.

---

## Proposed Modes & Key Mappings

### Mode 1: Nested WASD Categories (`NESTED`)
A two-level menu where the first keypress selects a category (Delete, Dissolve, Merge, Extras), and the second keypress selects the specific action.

*   **Initial HUD State (Category Selector):**
    *   `A` ➔ **Delete Category**
    *   `D` ➔ **Dissolve Category**
    *   `S` ➔ **Merge Category**
    *   `W` ➔ **Extras Category**
*   **Sub-Menus (W, A, S, D, Q mapping):**
    *   **Delete Category (`A`):**
        *   `A` ➔ Vertices (`mesh.delete(type='VERT')`)
        *   `W` ➔ Edges (`mesh.delete(type='EDGE')`)
        *   `D` ➔ Faces (`mesh.delete(type='FACE')`)
        *   `S` ➔ Only Edges & Faces (`mesh.delete(type='EDGE_FACE')`)
        *   `Q` ➔ Only Faces (`mesh.delete(type='ONLY_FACE')`)
    *   **Dissolve Category (`D`):**
        *   `A` ➔ Vertices (`mesh.dissolve_verts`)
        *   `W` ➔ Edges (`mesh.dissolve_edges`)
        *   `D` ➔ Faces (`mesh.dissolve_faces`)
        *   `S` ➔ Collapse Edges (`mesh.edge_collapse`)
        *   `Q` ➔ Limited Dissolve (`mesh.dissolve_limited`)
    *   **Merge Category (`S`):**
        *   `A` ➔ Merge Center (`mesh.merge(type='CENTER')`)
        *   `W` ➔ Merge At Cursor (`mesh.merge(type='CURSOR')`)
        *   `D` ➔ Merge By Distance (`mesh.remove_doubles`)
        *   `S` ➔ Merge Collapse (`mesh.merge(type='COLLAPSE')`)
    *   **Extras Category (`W`):**
        *   `A` ➔ Delete Linked (`rextools3.delete_linked_ex`)
        *   `W` ➔ Checker Dissolve (`mesh.checker_dissolve`)
        *   `D` ➔ Loop Dissolve (`rextools3.loop_dissolve_ex`)
        *   `S` ➔ Fill Loop Region (`rextools3.fill_loop_inner_region`)
*   **Navigation:** Pressing `ESC`, `BACKSPACE`, or `SPACE` while in a sub-category returns to the main category selector.

---

### Mode 2: Keyboard Grid Layout (`GRID`)
A flat menu displaying a visual grid matching the keyboard keys. Single-key press triggers the action immediately.

*   **Row 1 (Q, W, E, R):**
    *   `Q` ➔ Delete Vertices
    *   `W` ➔ Delete Edges
    *   `E` ➔ Delete Faces
    *   `R` ➔ Delete Linked
*   **Row 2 (A, S, D, F):**
    *   `A` ➔ Dissolve Vertices
    *   `S` ➔ Dissolve Edges
    *   `D` ➔ Dissolve Faces
    *   `F` ➔ Checker Dissolve
*   **Row 3 (Z, X, C, V):**
    *   `Z` ➔ Merge Center
    *   `X` ➔ Merge By Distance
    *   `C` ➔ Loop Dissolve
    *   `V` ➔ Fill Loop Region

---

### Mode 3: Hold-and-Press Modifiers (`MODIFIER`)
A single-level WASD key mapping where modifier keys held on the keyboard dynamically swap the operations.

*   **No Modifier (Base Delete):**
    *   `A` ➔ Delete Vertices
    *   `W` ➔ Delete Edges
    *   `D` ➔ Delete Faces
    *   `S` ➔ Only Edges & Faces
*   **Holding `Shift` (Dissolve Mode):**
    *   `A` ➔ Dissolve Vertices
    *   `W` ➔ Dissolve Edges
    *   `D` ➔ Dissolve Faces
    *   `S` ➔ Limited Dissolve
*   **Holding `Alt` (Merge Mode):**
    *   `A` ➔ Merge Center
    *   `W` ➔ Merge At Cursor
    *   `D` ➔ Merge By Distance
    *   `S` ➔ Merge Collapse
*   **Holding `Ctrl` (RexTools Extras):**
    *   `A` ➔ Delete Linked
    *   `W` ➔ Checker Dissolve
    *   `D` ➔ Loop Dissolve
    *   `S` ➔ Fill Loop Region

---

## Verification Plan

### Manual Verification
1. Open Blender Preferences ➔ Add-ons ➔ RexTools3.
2. In the "Shortcuts" tab, verify that `Quick Delete Mode` dropdown is visible and contains Nest, Grid, and Modifier modes.
3. Enter Edit Mode in a Mesh object.
4. Press `X` to invoke the modal under each preference mode, verifying the correct HUD drawing and keyboard shortcut execution.
