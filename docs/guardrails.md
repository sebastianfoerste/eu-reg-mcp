# Guardrails: what "review-gated" means here

Every response carries its framing:

- **Register results** are facts from a public register, returned with the snapshot date. A `removed` change record means the entry left the register export; the register does not state why.
- **Lint and classification outputs** are candidate flags from deterministic rules, **pending human legal review**. Extraction artifacts exist.

Nothing this server returns is a legal assessment of any entity or legal advice — that is a design contract, not a disclaimer. The text lives in the server instructions and in the `notice` field of each response (see `src/eu_reg_mcp/server.py`, `register.py`, `integrations.py`).
