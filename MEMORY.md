# MEMORY.md

## Active Projects

### ClearBoard
- **Location:** `/Users/clawdbotagent/workspace/ClearBoard`
- **Description:** Cross-platform screen annotation utility for macOS and iPadOS
- **Tech Stack:** SwiftUI, PencilKit, Core Graphics, Carbon (hotkeys)
- **Status:** Active development - UI design updated
- **Goal:** Build transparent overlay for real-time drawing/annotation over any app

## Recent Work

### Feb 1, 2025 - UI Redesign with Passthrough
- Created new glassmorphism toolbar design (`ToolbarView.swift`)
- Added passthrough toggle to toolbar
- Implemented `PassthroughController` for click-through mode
- Updated UX_DESIGN.md with new layout and passthrough documentation

### Feb 1, 2025 - Updated Toolbar Features (Draggable + Color Picker)
- **Position:** Top-right by default, draggable anywhere
- **Draggable:** Entire header area drags the window
- **Vertical color grid:** 2 columns × 4 rows (8 colors)
- **Color names:** Displayed next to each swatch
- **Color picker:** System SwiftUI ColorPicker (press palette button)
- **Enhanced colors:** Red, Orange, Yellow, Green, Blue, Purple, Pink, White
- **Larger swatches:** 22px when selected, 18px when not
- **Accent selection:** Blue highlight with rounded rectangle background
- **Frosted glass:** 20pt rounded corners, 15pt shadow
- **Collapsed:** 48px width | **Expanded:** 280px width

### Feb 1, 2025 - Integration
- **OverlayEngine.swift:** Added `createToolbarWindow()` method
- New SwiftUI toolbar now shows at top-right when overlay activates
- Removed old bottom HUD (or kept as secondary toolbar)
- Uses `ToolType` enum for tool selection compatibility

## Technical Notes

### macOS Overlay Implementation
- Uses `NSWindow` with `.borderless`, `.nonactivatingPanel` style
- Transparent background, click-through toggle
- Window level: `.screenSaver` for topmost overlay
- Carbon API for global hotkeys (Cmd+Shift+O for toggle, Cmd+Shift+P for passthrough)

### Drawing Tools
- Pen, marker, eraser, shapes (arrow, rectangle, circle)
- Laser pointer with fade animation
- PencilKit integration for iPadOS (pressure sensitivity)
- Undo/redo via `PKCanvasView.undoManager`

### Export Formats
- PNG (screen capture + annotations)
- PDF (vector-based)
- SVG (planned)

## Next Actions
1. Update macOS on Mac mini
2. Install Xcode
3. Run `xcode-select -s /Applications/Xcode.app/Contents/Developer`
4. Build ClearBoard project
5. Test overlay and drawing functionality
6. Integrate new ToolbarView into OverlayEngine
