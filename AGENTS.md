# AGENTS.md

Read `CONTRIBUTING.md` in full. Every section applies to AI-authored changes.

`CONTRIBUTING.md` is framed around "before submitting a PR". For agents, the equivalent gate is **before every push and before reporting any code task as complete**: run the four CI checks and the self-review checklist there, even when the user will be the one to submit the PR. Don't rely on CI to surface formatting, lint, or type errors after the fact.

Common AI-generation artifacts to catch in your own output:

- Paragraph-length docstrings on trivial helpers.
- Getter methods that just return an attribute.
- "Just in case" parameters, fields, or branches with no current caller.
- Extra abstraction added because it feels structurally clean, not because anything reuses it.
- Comments that explain *what* the code does rather than *why*.
