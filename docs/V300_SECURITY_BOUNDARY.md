# v3.0.0 Security and Recovery Boundary

- Browser project data remains local unless explicitly exported or sent to a configured backend.
- The local runner listens only on 127.0.0.1 and requires origin-bound pairing.
- No arbitrary shell endpoint is exposed.
- Reset planning never deletes records by itself.
- Protected or complete-workspace reset plans require backup confirmation and the exact phrase `RESET WORKBENCH`.
- Handoff packets must be revalidated by the destination application.
