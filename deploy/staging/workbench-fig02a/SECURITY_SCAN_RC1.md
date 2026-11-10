# Security scan — Workbench FIG-02A staging candidate rc1

**Scope:** staging image `sc-workbench-staging:14.0.0-fig02a-rc1-7cfbdf0c6ad0` (Contabo,
`sha256:ad6671df…`) and a CI rebuild of the same revision. Report-only; no dependency was changed
because of these results.

**Scanner:** Trivy 0.76.1 (release tarball, sha256 `c7cbe313…`), vulnerability DB updated
2026-11-10T01:02:55Z. Workflow: `.github/workflows/workbench-staging-security-scan.yml`, run
[42757426292](https://github.com/Content-Catalyst-LLC/sustainable-catalyst-workbench/actions/runs/42757426292)
(artifact `workbench-staging-security-scan`, 90 days).

## Rebuild equivalence

| Check | Result |
|---|---|
| Image ID | **Different.** CI `sha256:3dbb4c19…` vs Contabo `sha256:ad6671df…`. Every CI run produces a new ID, so the rebuild is **not** the same image |
| Layers | 4/11 identical (the digest-pinned python base). The apt+Chrome, WORKDIR, requirements, pip, `COPY . .`, useradd and Julia layers differ (file timestamps and package-index state at build time) |
| SBOM component set | **Identical** (282 = 282 name@version, including Debian 12.15, Chrome for Testing 157.0.8103.50, Julia 1.11.9, CPython 3.12.16) |

Conclusion: the CI rebuild has the same packages as the Contabo image but is not byte-identical.
The vulnerability results below come from scanning the Contabo SBOM and the CI rebuild image. The
two agree exactly for Debian and Python packages.

## Findings

| Source | Critical | High | Medium | Low | Unknown | Fixed version available |
|---|---|---|---|---|---|---|
| Debian 12.15 OS packages | 4 | 81 | 221 | 218 | 21 | **0** (all `affected`, `fix_deferred` or `will_not_fix`) |
| Python packages | 0 | 0 | 6 | 1 | 0 | 7 |
| Julia stdlib test manifests | 16 | 34 | 43 | 6 | 0 | n/a. **False positives** (see below) |

### Critical (Debian, no fixed package in bookworm)

| CVE | Package | Status | Assessment |
|---|---|---|---|
| CVE-2026-58016 | libglib2.0-0 2.74.6-2+deb12u9 | fix_deferred | D-Bus introspection XML parsing. No D-Bus in the container. Pulled in by Chrome's GTK dependencies. Low exposure |
| CVE-2025-7458 | libsqlite3-0 3.40.1-2+deb12u2 | affected | Integer overflow triggered by crafted SQL. Python's `sqlite3` uses it for the project store, but Workbench issues its own parameterised SQL. Low exposure; track |
| CVE-2026-6653 | libxml2 2.9.14+dfsg-1.3~deb12u6 | fix_deferred | Use-after-free from crafted XML. No Workbench path parses untrusted XML with the system libxml2 (lxml wheels bundle their own). Low to medium; track |
| CVE-2023-45853 | zlib1g 1:1.2.13.dfsg-1 | will_not_fix | Affects minizip `zipOpenNewFileInZip4_6`, which Debian does not ship in zlib1g. **False positive for runtime** |

The high findings are concentrated in libglib2.0, libxml2, libcurl4, libsqlite3, libexpat1, libtiff6,
util-linux (8 binaries), libcups2, libxi6, systemd, ncurses and perl-base. None has a bookworm fix.
Most of these packages come from Chrome's desktop dependencies (GTK, CUPS, X11, systemd).

### Python (fixed versions exist; not applied)

| Package | Installed | Findings | Fixed in | Assessment |
|---|---|---|---|---|
| pip | 25.0.1 (from the base image) | 5 medium, 1 low | 26.2.0 | Not used at runtime. Remove from the runtime image or upgrade at build time |
| pytest | 8.4.2 (from `requirements.txt`) | CVE-2025-71176 medium | 9.0.3 | Test dependency shipped in the runtime image. Move to a dev/test requirements file |

### False positives

- **Julia (16 critical / 34 high):** every target is
  `usr/local/julia/share/julia/stdlib/v1.11/{Pkg/test/test_packages/ShouldPreserveSemver,Tar/test/perf}/Manifest.toml`.
  These are test fixtures that pin old JLL versions; Julia does not load them. The JLLs Julia
  actually loads (checked in the staging image) are LibCURL 8.6.0, MbedTLS 2.28.6, LibSSH2 1.11.0,
  Zlib 1.2.13 and nghttp2 1.59.0, not the flagged 7.84.0 / 2.28.0 / 1.10.2 / 1.2.11.
- **zlib CVE-2023-45853:** minizip only (above).

## Coverage gaps

- **Chrome for Testing 157.0.8103.50** is a vendor binary, and Trivy does not report advisories for
  it. Track Chrome stable security releases and bump `CHROME_VERSION`/`CHROME_SHA256`.
- **Julia's bundled native libraries** are not scanned. MbedTLS 2.28.x reached end of life. The
  Workbench Julia path performs numerical work only, but this needs a decision before production.
- The first two SBOM versions under-reported OS findings. They lacked the OS component and
  source-package data (v1: 0 critical/high; v2: 1/11). v3 (`sha256 f8effcad…`) matches the image scan.

## Recommendations (not applied; each needs a reviewed change)

1. Exclude `pytest` and `pip` from the runtime image.
2. Evaluate `chrome-headless-shell` in place of full Chrome. It drops the GTK, CUPS, X11 and systemd
   dependencies behind most OS findings, but it needs Kaleido/choreographer validation.
3. Evaluate a Debian 13 (trixie) base when Python 3.12 slim-trixie is pinned and the regression suite
   passes.
4. Decide on Julia (upgrade, remove from the FIG-02A image, or accept the risk with justification).
5. Scan the **production** image (`sc-workbench:uvr-01-3-7`) the same way. It was not scanned here.
