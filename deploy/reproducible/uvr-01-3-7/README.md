# Reproducible build: sc-workbench:uvr-01-3-7

`backend/` on this branch is byte-identical to `/app` in the production image `sc-workbench:uvr-01-3-7`. The two editor backup files are the only exception: `erw_v080.py.pre-fix` and `main.py.pre-erw-v13816.bak`.

`backend/requirements.txt` gives version ranges only. A fresh build from `backend/Dockerfile` therefore picks up whatever is newest at build time. The production image was also assembled in increments, with files copied in on top of earlier images, so its layers cannot be rebuilt bit for bit. This recipe reproduces its contents instead:

- **Base images:** `python:3.12.15-slim-trixie` and `julia:1.11.9-bookworm`, pinned by digest. These are the Python, Debian and Julia versions in the production image.
- **Python packages:** `constraints.txt` is `pip freeze` of the production image, without `pip`.
- **Application files:** `backend/`, unchanged. This recipe keeps the build files out of `backend/` so that tree stays identical to production.

```
deploy/reproducible/uvr-01-3-7/build.sh sc-workbench-ci:<commit>
```

The script fails if the installed packages differ from `constraints.txt`.

**Verified on 2026-11-20.** The built image matched production on `pip freeze`, Python, Julia and Debian versions. Its `/app` matched production, apart from the two backup files.
