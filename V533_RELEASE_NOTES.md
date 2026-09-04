# Sustainable Catalyst Workbench v5.3.3

## Homepage & Workbench Experience Integration Hardening

v5.3.3 is the stabilization release for the v5.3.x public interface line.

### Fixed

- Removed the homepage carousel's use of `scrollIntoView()`, which could move the entire page vertically when the active feature changed.
- Active feature movement is now constrained to the horizontal capability rail with `rail.scrollTo({left: ...})` only when the rail actually overflows.
- Initial Workbench initialization does not scroll the page or the feature rail.
- Automatic feature rotation does not modify the URL hash, focus state, or window scroll position.
- Added a front-page compatibility guard so `[sc_workbench_v530_showcase]` cannot accidentally restore the tall legacy v5.3.0 showcase on the homepage.
- Integrated the homepage width/spacing contract into plugin CSS for both the explicit `.cch-workbench-showcase` wrapper and a bare Workbench shortcode directly under `.cc-home-v4`.
- Synchronized primary shortcode and public interface version identity to v5.3.3.

### Preserved

- Compact rotating Graph / CAS / Sound / Form / Prototype showcase.
- Permanent **Open Workbench →** CTA.
- Advanced graph presentation introduced in v5.3.2.
- `[sc_workbench_experience]` public page surface.
- Backend/CAS/graph APIs remain on the certified v5.3.0 FastAPI runtime.

### Deployment

WordPress plugin update only. No Contabo backend rebuild is required.
