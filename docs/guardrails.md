# Guardrails: what "review-gated" means here

Every response carries its framing:

- **Register results** are facts from a public register, returned with the snapshot date. A `removed` change record means the entry left the register export; the register does not state why.
- **Lint and classification outputs** are candidate flags from deterministic rules, **pending human legal review**. Extraction artifacts exist.

The two prompts (`check_register_status`, `review_register_changes`) carry the same contract into the model's instructions: state the snapshot date, treat `similar_names` as non-matches, never guess why an entry was removed, and end with the register `notice`. Search `match` scores and `similar_names` similarities describe string matching only, never the entity.

Nothing this server returns is a legal assessment of any entity or legal advice — that is a design contract, not a disclaimer. The text lives in the server instructions and in the `notice` field of each response (see `src/eu_reg_mcp/server.py`, `register.py`, `integrations.py`).
