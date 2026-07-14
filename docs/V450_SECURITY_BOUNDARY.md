# Workbench v4.5.0 Security Boundary

The extension framework produces manifests, compatibility reports, registry entries, permission audits, hook contracts, lifecycle plans, developer scaffolds, security findings, and portable packages. It does not execute arbitrary extension code or authorize remote shells.

Installation, activation, updates, deactivation, and uninstall remain explicit human-controlled operations. Updates and uninstall require a verified backup. Uninstall requires the exact confirmation phrase `UNINSTALL WORKBENCH EXTENSION`.

Forbidden capabilities include shell execution, process spawning, unrestricted filesystem access, database administration, authentication or safety bypasses, secret access, autonomous device execution, automatic publication, and automatic certification.
