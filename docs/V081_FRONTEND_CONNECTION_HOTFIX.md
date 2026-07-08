# v0.8.1 Frontend Connection Hotfix

This hotfix fixes a front-end fallback notice issue in the WordPress plugin.

## Fixed

- The calculator tab no longer shows “Backend offline” during initial local registry hydration.
- When `/wp-json/sc-workbench/v1/tools` confirms that the FastAPI backend is online, the notice is cleared and replaced with a neutral connected message.
- The local calculator registry remains available as a fallback if the backend is actually unreachable.
- Existing opened calculator forms are not overwritten by later registry refreshes.

## Why this mattered

The admin test endpoint could report the Render backend as healthy while the public Workbench tab still displayed the offline fallback message. The underlying cause was front-end state handling, not the Gemini/Render backend connection.
