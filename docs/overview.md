# Overview

An MCP server that gives AI agents **cited, review-gated grounding in EU regulation**. Install and the tool list: [README](../README.md). Parameters, data sources and errors: [tools.md](tools.md).

## Who it's for

- **Crypto-asset compliance and legal teams** looking up entities on the ESMA interim MiCAR register (white papers, authorised CASPs, non-compliant entities) and tracking what changes on it, including removals.
- **Teams preparing MiCAR white papers** who want a deterministic Annex I–III check of a draft that returns cited candidate findings.
- **Teams assessing AI systems under the EU AI Act** who want a first-pass risk-tier classification with pinpoint Art. 5 / Annex III / GPAI citations.

It does not replace legal review: its outputs are register facts or candidate flags for a human to assess (see [Guardrails](guardrails.md)).

## Try it now

There is no hosted playground. eu-reg-mcp is a [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server, so you try it by adding it to your own MCP client — the README's [Quick start](../README.md#quick-start) has the commands for Claude Code, and [clients.md](clients.md) the configuration for Claude Desktop and other clients. Then ask your assistant:

- "Is `<entity>` on the MiCAR register, and what format is its white paper?"
- "What changed on the MiCAR register recently — any removals?"
- "Classify this AI system under the EU AI Act" (paste a system profile; call with an empty string to get the schema).

The first two work without extras; the third needs the `classify` extra.

For a scripted Claude Code session on a life insurer's pricing model, with its recording protocol, see [demo/claude-code-life-insurer.md](demo/claude-code-life-insurer.md) (script and protocol; run not yet recorded).

## Example output

> **Synthetic data.** Produced on 2026-10-27 by calling this repo's `search_micar_register` tool function against the **synthetic test fixtures** in `tests/fixtures/`, not the live register. The entity and its LEI are invented. Output shape is what a live call returns; values are not.

`search_micar_register(query="testnet")`, abridged: the response also has `data_age_days`, `stale`, `observatory_snapshot`, `offset`, `similar_names` and `warnings`, and each result `entry_id` and `esma_source_url`:

```json
{
  "snapshot_date": "2026-07-07",
  "total_matches": 1,
  "results": [
    {
      "register": "other-wp",
      "entity_name": "Example Testnet GmbH",
      "lei": "529900EXAMPLELEI0002",
      "member_state": "LU",
      "authority": "CSSF",
      "whitepaper_url": "WWW.EXAMPLE-TESTNET.EXAMPLE",
      "format_class": "unspecified",
      "register_last_update": "01/01/2026",
      "match": {
        "score": 0.85,
        "basis": "whole_words"
      }
    }
  ],
  "truncated": false,
  "next_offset": null,
  "notice": "Facts from the public ESMA interim MiCAR register (Art. 109 MiCAR) as mirrored by the MiCAR Register Observatory. No legal assessment of any entity; not legal advice."
}
```

`match` says how the query string matched the name or LEI; it says nothing about the entity. `micar_register_changes(change_type="removed")` returns the same kind of cited record (snapshot date, register, entity) and notes that *"the register itself does not state why"* an entry was removed. With the extras installed, the lint and classify tools cite the provision behind each finding, for example `Anhang I Teil A MiCAR` (MiCAR Annex I, Part A), `Art. 5(1)(f) AIA`, `Annex III(4)(a) AIA`, and `Art. 51 AIA` for a general-purpose AI model with systemic risk. Sample output from synthetic inputs: [tools.md](tools.md#sample-lint-and-classify-output).

## Why not just ask an LLM?

An ungrounded model can invent register entries or provisions. Here, register answers come from a dated snapshot of the public register, and lint/classification output comes from deterministic rules with citations. **Review-gated** means the output is a candidate flag pending human legal review — never a legal assessment or legal advice. Details: [guardrails.md](guardrails.md).

## Part of the EU regulation as code suite

By [sebastianfoerste](https://github.com/sebastianfoerste):

- [awesome-eu-fintech-regulation](https://github.com/sebastianfoerste/awesome-eu-fintech-regulation)
- [contract-review-eval-harness](https://github.com/sebastianfoerste/contract-review-eval-harness)
- [legal-function-operating-system](https://github.com/sebastianfoerste/legal-function-operating-system)
- [eu-ai-act-classifier](https://github.com/sebastianfoerste/eu-ai-act-classifier)
- [micar-whitepaper-linter](https://github.com/sebastianfoerste/micar-whitepaper-linter)
- **eu-reg-mcp** (this repo)
- [micar-register-observatory](https://github.com/sebastianfoerste/micar-register-observatory)
