# Workbench v2.9.0 Security and Review Boundary

- Browser records remain local unless the user deliberately exports or submits them.
- The Go Runner listens only on `127.0.0.1:8787`, requires pairing, and binds tokens to the requesting browser origin.
- There is no arbitrary shell endpoint.
- Documentation tasks are allowlisted version and discovery calls only.
- Generated documents and hashes do not prove correctness, authenticity, approval, compliance, or certification.
- Source data, revisions, evidence links, signatures, standards, and release gates require independent controlled review.
