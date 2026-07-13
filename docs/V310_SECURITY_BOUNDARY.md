# Workbench v3.1.0 Storage and Security Boundary

- Anonymous projects remain in the current browser profile.
- Browser storage is not uploaded unless a signed-in user explicitly saves or synchronizes a hybrid/WordPress project.
- WordPress projects and revisions are private custom post records.
- REST writes require an authenticated WordPress REST nonce and `edit_posts` capability.
- Project access is restricted to the record owner unless the current user can edit other authors' posts.
- Synchronization reports hash conflicts and supports explicit local, remote, newest, or manual strategies.
- Browser and server revisions are bounded to reduce uncontrolled storage growth.
- Project records and revisions are workflow records, not certificates of technical correctness, compliance, safety, or professional approval.
- Users should export project packages before migration, cleanup, account changes, or destructive recovery operations.
