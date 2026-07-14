# Workbench v4.1.0 Security Boundary

- All organization, team, project, invitation, and activity records are private by default.
- Hosted records require an authenticated WordPress user with appropriate capabilities.
- Invitation records persist token hashes rather than raw tokens.
- Invitations are never accepted automatically.
- Roles are never escalated automatically.
- Project deletion, publication, overwrite, and conflict resolution require human authorization.
- Team exports omit secrets and redact member identifiers unless explicitly included.
- Offline and browser-local modes do not imply hosted authentication.
- Workbench does not provide remote shells or arbitrary command execution.
