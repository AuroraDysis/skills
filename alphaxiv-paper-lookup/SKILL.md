---
name: alphaxiv-paper-lookup
description: Look up any arxiv paper on alphaxiv.org to get a structured AI-generated overview. This is faster and more reliable than trying to read a raw PDF.
---

# AlphaXiv Paper Lookup

Look up any arxiv paper on alphaxiv.org to get a structured AI-generated overview. This is faster and more reliable than trying to read a raw PDF.

## When to Use

- User shares an arxiv URL (e.g. `arxiv.org/abs/2401.12345` or `arxiv.org/abs/gr-qc/9908012`)
- User mentions a paper ID (e.g. `2401.12345` or `gr-qc/9908012`)
- User asks you to explain, summarize, or analyze a research paper
- User shares an alphaxiv URL (e.g. `alphaxiv.org/overview/2401.12345`)

## Workflow

### Step 1: Extract the paper ID

arXiv has two ID formats:

- **New format** (April 2007+): `YYMM.NNNNN` (e.g. `2401.12345`)
- **Old format** (pre-2007): `category/YYMMNNN` (e.g. `gr-qc/9908012`, `hep-th/0001234`)

Parse the paper ID from whatever the user provides:

| Input                                          | Paper ID         |
| ---------------------------------------------- | ---------------- |
| `https://arxiv.org/abs/2401.12345`             | `2401.12345`     |
| `https://arxiv.org/pdf/2401.12345`             | `2401.12345`     |
| `https://arxiv.org/abs/gr-qc/9908012`          | `gr-qc/9908012`  |
| `https://arxiv.org/pdf/gr-qc/9908012`          | `gr-qc/9908012`  |
| `https://alphaxiv.org/overview/2401.12345`     | `2401.12345`     |
| `https://alphaxiv.org/overview/gr-qc/9908012`  | `gr-qc/9908012`  |
| `2401.12345v2`                                 | `2401.12345v2`   |
| `2401.12345`                                   | `2401.12345`     |
| `gr-qc/9908012`                                | `gr-qc/9908012`  |
| `hep-th/0001234v2`                             | `hep-th/0001234v2` |

### Step 2: Fetch the machine-readable report

```bash
curl -s "https://alphaxiv.org/overview/{PAPER_ID}.md"
```

This returns the intermediate machine-readable report — a structured, detailed analysis of the paper optimized for LLM consumption. One call, plain markdown, no JSON parsing.

If this returns 404, skip to Step 3.

### Step 3: Fetch the full paper text

Fetch the full paper text if:
- The overview returned 404 in Step 2, OR
- The overview doesn't contain the specific information the user is asking about (e.g. a particular equation, table, or section)

```bash
curl -s "https://alphaxiv.org/abs/{PAPER_ID}.md"
```

This returns the full extracted text of the paper as markdown.

If this also returns 404, direct the user to the PDF at `https://arxiv.org/pdf/{PAPER_ID}` as a last resort.

## Error Handling

- **404 on both Step 2 and Step 3**: Paper not yet processed on alphaxiv. Fall back to the arxiv PDF.

## Notes

- No authentication required — these are public endpoints.
