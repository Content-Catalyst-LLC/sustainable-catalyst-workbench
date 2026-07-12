# Sustainable Catalyst Workbench v1.9.1 Release Notes

## Editor-first browser execution patch

Workbench Code Studio now behaves like a browser-based coding lab. Users type or paste code into the editor and click Run; they no longer need to navigate the project through terminal commands for ordinary execution.

### Added

- Editor-first default layout
- Side-by-side code and output panes
- Large direct Run button
- Automatic save before execution
- Automatic runtime loading
- Language-aware runnable-file selector
- Line numbers
- Ctrl/Command + Enter shortcut
- Clear output control
- Visible run state

### Preserved

- JavaScript, Python, R, and SQL browser execution
- Browser-local project storage
- Files and project export
- Structured tables and charts
- Runtime limits and static safety checks
- Advanced command-line console
- Standalone terminal shortcode

### Safety

WordPress and FastAPI continue not to execute user-submitted browser code. Project files remain on the visitor device unless explicitly downloaded or exported.
