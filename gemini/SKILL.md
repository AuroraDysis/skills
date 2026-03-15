---
name: gemini
description: Use when the user asks to run Gemini CLI (gemini -p, gemini --prompt, gemini --resume) or references Google Gemini CLI for code analysis, refactoring, or automated editing
---

# Gemini Skill Guide

## Running a Task
1. Default to model `gemini-3.1-pro-preview`. Do NOT ask the user for model — use this default automatically unless the user explicitly specifies otherwise. Available models: `gemini-3.1-pro-preview`, `gemini-3-flash-preview`, `gemini-2.5-pro`, `gemini-2.5-flash`, `gemini-2.5-flash-lite`.
2. Select the approval mode required for the task; default to `--approval-mode plan` (read-only) unless edits or broader access are necessary.
3. Assemble the command with the appropriate options:
   - `-m, --model <MODEL>`
   - `-p, --prompt <PROMPT>` (non-interactive / headless mode — required for programmatic use)
   - `--approval-mode <default|auto_edit|yolo|plan>`
   - `-s, --sandbox` (enable sandbox)
   - `-r, --resume <latest|INDEX>` (resume a previous session)
   - `-o, --output-format <text|json|stream-json>`
   - `--include-directories <DIR1>,<DIR2>` (add extra workspace directories)
   - `-y, --yolo` (shorthand for `--approval-mode yolo`)
   - `-d, --debug` (enable debug mode)
4. Always use `-p` / `--prompt` for non-interactive execution so the command runs headlessly and returns output to this session.
5. Run the command, capture output, and summarize the outcome for the user.
6. **After Gemini completes**, inform the user: "You can resume this Gemini session at any time by saying 'gemini resume' or asking me to continue with additional analysis or changes."

### Quick Reference
| Use case | Approval mode | Key flags |
| --- | --- | --- |
| Read-only review or analysis | `plan` | `--approval-mode plan -p "prompt"` |
| Apply local edits (auto-approve edits) | `auto_edit` | `--approval-mode auto_edit -p "prompt"` |
| Full auto-approve all actions | `yolo` | `--approval-mode yolo -p "prompt"` |
| Resume most recent session | Inherited from original | `--resume latest -p "follow-up prompt"` |
| Resume specific session | Inherited from original | `--resume <INDEX> -p "follow-up prompt"` |
| Run in a different directory | Match task needs | `cd <DIR> && gemini --approval-mode plan -p "prompt"` |
| Structured output for scripting | Match task needs | `-o json -p "prompt"` |

## Following Up
- After every `gemini` command, immediately use `AskUserQuestion` to confirm next steps, collect clarifications, or decide whether to resume with `--resume latest`.
- When resuming, use: `gemini --resume latest -p "follow-up prompt"`. The resumed session automatically uses the same model and approval mode from the original session.
- Restate the chosen model and approval mode when proposing follow-up actions.

## Critical Evaluation of Gemini Output

Gemini is powered by Google models with their own knowledge cutoffs and limitations. Treat Gemini as a **colleague, not an authority**.

### Guidelines
- **Trust your own knowledge** when confident. If Gemini claims something you know is incorrect, push back directly.
- **Research disagreements** using WebSearch or documentation before accepting Gemini's claims. Share findings with Gemini via resume if needed.
- **Remember knowledge cutoffs** - Gemini may not know about recent releases, APIs, or changes that occurred after its training data.
- **Don't defer blindly** - Gemini can be wrong. Evaluate its suggestions critically, especially regarding:
  - Model names and capabilities
  - Recent library versions or API changes
  - Best practices that may have evolved

### When Gemini is Wrong
1. State your disagreement clearly to the user
2. Provide evidence (your own knowledge, web search, docs)
3. Optionally resume the Gemini session to discuss the disagreement. **Identify yourself as Claude** so Gemini knows it's a peer AI discussion. Use your actual model name:
   ```bash
   gemini --resume latest -p "This is Claude (<your current model name>) following up. I disagree with [X] because [evidence]. What's your take on this?"
   ```
4. Frame disagreements as discussions, not corrections - either AI could be wrong
5. Let the user decide how to proceed if there's genuine ambiguity

## Error Handling
- Stop and report failures whenever `gemini --version` or a `gemini -p` command exits non-zero; request direction before retrying.
- Before you use high-impact flags (`--approval-mode yolo`, `--approval-mode auto_edit`) ask the user for permission using AskUserQuestion unless it was already given.
- When output includes warnings or partial results, summarize them and ask how to adjust using `AskUserQuestion`.
