# Claude Code demo: a life insurer's pricing model

> **Status:** script and recording protocol only. No run has been recorded yet. The metadata, characterisation, transcript and review sections below stay empty until the first run is pasted in, unchanged. This script and protocol were drafted with AI assistance (Claude) and adopted by the user on [date].

## Purpose

This demo shows Claude in Claude Code using eu-reg-mcp to classify an insurer's AI system under the EU AI Act, and to answer with each obligation cited to its article and the date it applies. It also shows where the tools stop. Claude has to turn a plain description into the structured facts the classifier runs on, and characterising a system that way is a legal judgment, so the transcript shows those facts and labels them for review.

In this document, "the user" is the person who runs the session and publishes the recording.

## Setup

### 1. Check that the install fix is on `main`

Record only once [`pyproject.toml`](../../pyproject.toml) on `main` pins `mcp>=1.2,<2`. Without the pin, uv installs mcp 2.x, which no longer has the `mcp.server.fastmcp` module this server imports, and the server does not start.

### 2. Install in a new, empty directory outside any project

Claude Code loads instruction files (`CLAUDE.md` and its variants) from the working directory and from every parent directory, as well as the user's own `~/.claude/CLAUDE.md`. A demo directory under a project would bring that project's instructions into the session, so create it inside a new temporary directory. `claude mcp add` registers the server for the current directory by default, so run it there. The install command is the one in the [README](../../README.md#install), unchanged:

```bash
cd "$(mktemp -d)" && mkdir eu-reg-demo && cd eu-reg-demo
pwd
claude mcp add eu-reg -- uvx --from 'eu-reg-mcp[lint,classify] @ git+https://github.com/sebastianfoerste/eu-reg-mcp' eu-reg-mcp
claude mcp list
```

User-level settings still apply in any directory: the user's own instructions, plugins, skills, hooks and other MCP servers. They are not switched off for the demo. The metadata table records what was active (see [Capture and publish](#capture-and-publish)).

`claude mcp list` health-checks the server, and `eu-reg` must show as connected. The first start is slow while uv installs the linter and the classifier. This check starts the server but calls no tool. Do not try the prompt, or any classify call, before the recorded run.

### 3. Record the versions

Immediately before starting the session, run this in the same directory and keep the output for the metadata table:

```bash
date -u '+%Y-%m-%d %H:%M UTC'
claude --version
claude mcp get eu-reg
uvx --from 'eu-reg-mcp[lint,classify] @ git+https://github.com/sebastianfoerste/eu-reg-mcp' python -c '
import importlib.metadata as m, json
for d in ("eu-reg-mcp", "eu-ai-act-classifier", "micar-whitepaper-linter"):
    url = json.loads(m.distribution(d).read_text("direct_url.json") or "{}")
    print(d, url.get("vcs_info", {}).get("commit_id", "no commit recorded"))
'
```

- `claude --version` prints the Claude Code version.
- `claude mcp get eu-reg` prints the server command Claude Code will start, which should be the README command.
- The `uvx` command prints the commit uv installed each repository from, as uv records it in the package metadata (`direct_url.json`). It uses the same `--from` value as the server. The micar-whitepaper-linter commit is recorded for completeness; this prompt is not expected to call the linter.

Run the `uvx` command again right after the run. If the two outputs differ, record both.

The model name is read inside the session with `/status` after the run (see [Capture and publish](#capture-and-publish)).

## The prompt

Start Claude Code in the same directory with shell, file-editing and web tools switched off:

```bash
claude --disallowedTools "Bash,Edit,Write,NotebookEdit,WebFetch,WebSearch"
```

Denying a permission prompt during the run would stop Claude until the user tells it how to proceed, so these tools are removed before the run starts. Tools that need no permission prompt stay available.

Send this as the first message, exactly as written:

```text
A German life insurer will price term-life premiums with an in-house gradient-boosted model trained on applicant health questionnaires. Use the eu-reg tools to classify it under the AI Act, then give me a five-line board summary: each obligation with its article and the date it applies, and what a lawyer still has to decide.
```

## Recording protocol

### Pre-commitment

Before recording, the user fills in the date below and in the status block, then commits the change to `main` and pushes it, directly or through a merged pull request, so the commit stays reachable from `main`. Its SHA goes in the metadata table. The evidence that the commitment came first is the time GitHub recorded the push or the merge (in the repository's activity view, or on the pull request), not the commit date, which can be set locally.

> The user will publish the first run of this prompt verbatim, whether it completes or fails. If it fails, each later run is published below it, numbered in order, until one completes, and no run replaces another. Committed on [date].

### Rules for the run

- **One run.** The run is the first session in which the prompt is sent, and it is published. Nobody reruns to improve the output, edits the prompt, or replaces the run with a later attempt. A new run is made only after a failure, as defined below.
- **Fixed replies only.** The user types nothing except the prompt and these replies, which stay in the transcript:
  - If Claude asks a question before it gives the summary, the user replies once, with exactly: "Use your best characterisation and mark each assumption." If Claude asks again, the run ends there and is published as it stands.
  - If Claude Code still asks permission for a tool other than the eu-reg tools, the user denies it and sends exactly: "Continue without that tool."
- **Tool permissions.** The user approves each eu-reg tool call when Claude Code asks. Tools that run without a prompt (such as reading or searching files in the empty working directory, a task list, subagents or tool search) are not blocked, and they are recorded in the transcript as they occur. Claude may still add statements from its own knowledge; the [review of the summary](#review-of-the-summary) marks any article or date that no tool result contains. The metadata table records the start command and whether any tools were pre-approved in settings.
- **No interruptions.** The user does not interrupt the run. If it is interrupted anyway, it is published as it stands, and the interruption is not a failure.
- **A failure is an infrastructure fault that stops the run before the summary.** That means the eu-reg server does not start or connect, a tool call returns the install hint or an internal error instead of a result, or Claude Code or the model API ends the session with an error. A validation error that the classifier returns to Claude is part of the run, not a failure, and so is any error after which Claude still gives the summary. A failed run is published with a short note under [Failure note](#failure-note): what failed, the fix, and the commit that fixed it. The run made after the fix is added below it as "Run 2", labelled with that commit.
- **A wrong answer is not a failure.** If the summary is legally wrong or incomplete, it is published as it is, and the [review of the summary](#review-of-the-summary) says what is wrong.

### The characterisation needs review

The classifier does not read a description. It takes a `SystemProfile` of characterised facts, such as the operator roles (`roles`), the Annex III area (`annex_iii_area`) and the Art. 6(3) derogation facts, including profiling (`derogation`). The prompt leaves it to Claude to turn the description into that profile.

The classifier's own documentation assigns this step to a qualified reviewer. Its [claim ledger](https://github.com/sebastianfoerste/eu-ai-act-classifier/blob/a3757803538d3e152b5779eef167a5f625480051/docs/REGULATORY_CLAIM_LEDGER.md?plain=1#L11) records that classification of a real system "still depends on characterised facts, actor role and the applicable route", with the obligation "Qualified reviewer validates intake facts and legal characterisation". Its [README](https://github.com/sebastianfoerste/eu-ai-act-classifier/blob/a3757803538d3e152b5779eef167a5f625480051/README.md?plain=1#L137) says: "The engine applies rules to characterised facts and does not decide disputed intended purpose, operator role or factual deployment scope."

So every profile Claude passes to `classify_eu_ai_act_system` is copied, unchanged and in call order, into the section below under the label "Claude-proposed characterisation, reviewed by the user on [date]". The user then writes a review note: for each profile field, agree or disagree, and why. The review never changes the transcript or the profile. Disagreements go in the note.

### Capture and publish

1. A screen recording of the terminal is optional. The text record below is the one that counts.
2. After Claude's final answer, the user runs `/export` and saves the conversation to a file.
3. Then the user runs these commands in the session and copies what they show into the metadata table: `/status` for the Claude Code version and the model name, as displayed; `/context` for the instruction files loaded and the skills, agents and MCP tools available; `/mcp` for every MCP server connected; `/hooks` for any hooks configured.
4. The user re-runs the `uvx` version command from [Record the versions](#3-record-the-versions) in the shell.
5. The user keeps the session log. Claude Code writes each session as a `.jsonl` file under `~/.claude/projects/`, in the folder named after the working directory. It holds the input and output of every tool call. If that folder has a `tool-results` directory for this session, where Claude Code stores large tool output, those files belong to the log too. Where the export and the log differ, the log governs.
6. The export goes into [Transcript](#transcript) verbatim. The session log is committed beside this file as `claude-code-life-insurer.session.jsonl`, with any `tool-results` files in a folder `claude-code-life-insurer.tool-results/`. Where the export abbreviates tool output, the `.jsonl` holds the full text.

The transcript is verbatim, unedited tool output: no trimming, reformatting or cleaned-up JSON. Redact nothing except secrets (API keys, tokens, passwords). Mark each redaction `[REDACTED: secret]` and list it in the metadata table. Paths, error messages, denied tool calls and Claude's mistakes stay in. The setup needs no API key, so normally there is nothing to redact.

## Run metadata

| Field | Value |
| --- | --- |
| Recording date and time (UTC) | [YYYY-MM-DD HH:MM] |
| Pre-commitment commit | [SHA of the commit on `main` that dated the pre-commitment] |
| Working directory (`pwd`) | [path] |
| Session start command | [the `claude` command as typed] |
| Claude Code version (`claude --version`) | [version] |
| Model, as displayed in the session (`/status`) | [model name] |
| Server command (`claude mcp get eu-reg`) | [command] |
| eu-reg-mcp commit, resolved by uvx | [SHA] |
| eu-ai-act-classifier commit, resolved by uvx | [SHA] |
| micar-whitepaper-linter commit, resolved by uvx (installed, not expected to be called) | [SHA] |
| Commits after the run (same command) | [unchanged, or the new values] |
| Tools pre-approved in settings | [none, or which] |
| Instruction files loaded (`/context`) | [none, or each path] |
| Other MCP servers, plugins, skills and hooks active (`/mcp`, `/context`, `/hooks`) | [none, or which] |
| Redactions | [none, or each one] |
| Outcome | [complete, or failed: one line] |

## Claude-proposed characterisation

**Claude-proposed characterisation, reviewed by the user on [date]**

```json
[paste each SystemProfile JSON that Claude passed to classify_eu_ai_act_system, unchanged, in call order]
```

Review note: [for each profile field: agree or disagree, and why]

## Transcript

```text
[paste the verbatim transcript here]
```

## Review of the summary

[Reviewed by the user on [date]. First, each article or date in Claude's summary that no tool result contains. Then any legal error or omission in the summary.]

## Failure note

[Only if the run failed: what failed, the fix, and the commit that fixed it.]

## What this demo does not show

- **Legal advice.** Neither the classifier's output nor Claude's summary is a legal assessment of any insurer or product. Both are first-pass material for a lawyer's review, and every classify response carries the review notice defined in [`integrations.py`](../../src/eu_reg_mcp/integrations.py).
- **A real system.** The insurer and its model are invented for this demo. No real company, client or product is described.
- **A result that holds whatever the facts.** The classification is only as right as the characterised facts. A different, equally plausible characterisation, for example of the operator role, can change the tier or the obligations.
- **An answer drawn from the tools alone.** Claude can add articles, dates and reasoning from its own knowledge. The review of the summary marks what no tool result contains.
- **Reliability.** One prompt and one run show how this run went, not how Claude or the tools perform across cases.
- **Dates checked on the day.** The application dates the classifier returns come from its source data at the recorded commit; dates Claude adds itself are not from the tools. Neither is re-checked against the Official Journal on the recording day.
- **Other law.** The tools cover the AI Act and MiCAR only. Other law that applies to such a model, such as data protection or insurance supervision, is out of scope.
