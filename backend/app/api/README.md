# api/ — Week 3. You write the endpoint signatures.

Per CLAUDE.md, deciding what each endpoint accepts and returns is yours.
Claude can fill in FastAPI plumbing after the shapes are settled.

Think about, before typing:

- The client sends a schedule. Course codes? CRNs? A day?
- The response carries a route AND warnings. One object or two?
- A warning needs to say *which leg* and *why* — what does the frontend
  need in order to render that without a second round trip?
