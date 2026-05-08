# ebook-to-podcast

A Claude Code skill that splits an ebook (PDF or EPUB) into chapters, searches for authoritative reviews, and generates a structured book-review report — all from a single command.

> **Work in progress.** Chapter splitting and review report generation are complete. The original roadmap included auto-upload to [NotebookLM](https://notebooklm.google.com/) for AI podcast generation, but that step has been removed for now because the unofficial NotebookLM CLI is too unstable for reliable automation. You can still upload the exported chapter files to NotebookLM manually.

---

## What it does

1. **Split** — extracts chapters from a PDF (bookmarks) or EPUB (TOC), one `.txt` file per chapter
2. **Filter** — recommends which chapters to skip (front/back matter) and asks you to confirm
3. **Translate** — translates chapter titles into Chinese for non-Chinese books (used in file names)
4. **Search** — searches authoritative media, professional reviewers, and people mentioned in the book for their published opinions
5. **Report** — writes a structured Chinese book-review report (`书评报告.md`)
6. **Export** — copies the filtered chapters into a clean `chapters/` folder with bilingual file names

---

## Requirements

| Tool | Purpose |
|---|---|
| [Claude Code](https://claude.ai/claude-code) | Runs the skill |
| [`uv`](https://github.com/astral-sh/uv) | Runs `split_book.py` inline deps |

Python is not required separately — `uv` manages it automatically.

---

## Installation

### Option A — AI Agent install (recommended)

Paste the following into any Claude session:

```
Please install the ebook-to-podcast skill from https://github.com/noonsleeping/ebook-to-podcast
Clone the repo, run install.sh, and follow the prompts.
```

Claude will clone the repo, run `install.sh`, and walk you through the path configuration.

### Option B — Manual install

```bash
git clone https://github.com/noonsleeping/ebook-to-podcast.git
cd ebook-to-podcast
bash install.sh
```

`install.sh` will ask for two paths:

| Prompt | Default | Description |
|---|---|---|
| Inbox directory | `~/Downloads/eBooks/inbox` | Where you drop ebook files |
| Output root directory | `~/Downloads/eBooks` | Where project folders are created |

The installer copies skill files to `~/.claude/skills/ebook-to-podcast/` and writes your path choices to `~/.claude/skills/ebook-to-podcast/config.json`.

---

## Usage

1. Drop a `.pdf` or `.epub` into your inbox directory
2. Open Claude Code and type:

```
把inbox里的书处理一下
```

or in English:

```
Process the book in my inbox
```

Claude will handle everything from there, pausing to ask for your confirmation at each step.

---

## Skill triggers

The skill activates on any of these:

- "把 inbox 里的书处理一下"
- "把《xxx》拆分章节"
- "搜一下这本书的评价 / 书评报告"
- "Process the book in my inbox"
- "Split chapters for [book name]"
- Any instruction after dropping a `.pdf` or `.epub` into the inbox

---

## Output structure

```
~/Downloads/eBooks/<Book Title>/
├── chapters/               ← filtered chapters (.txt), bilingual file names
│   ├── Ch01 命运 (Chapter 1 Destiny).txt
│   ├── Ch02 「深刻的哲学问题」 (Chapter 2 "Deep Philosophical Questions").txt
│   └── ...
├── 书评报告.md             ← structured Chinese review report
└── .work/
    ├── chapters.json       ← full chapter manifest (skip flags, cn_title, etc.)
    └── chapters/           ← all raw chapter files (including skipped ones)
```

---

## File naming convention

**Non-Chinese books:**

| Type | Pattern |
|---|---|
| Numbered chapter | `Ch{NN} {cn_title} ({title}).txt` |
| Unnumbered (Intro / Epilogue / Preface) | `{cn_title}（{title}）.txt` |

**Chinese books:** `Ch{NN} {title}.txt` / `{title}.txt`

---

## Roadmap

- [x] Chapter splitting (PDF bookmarks + EPUB TOC)
- [x] Front/back matter filtering
- [x] Chapter title translation (Chinese)
- [x] Web review search (media + reviewers + subjects)
- [x] Structured review report
- [ ] NotebookLM auto-upload (blocked: unofficial CLI unstable)
- [ ] Audio generation pipeline

---

## License

MIT — see [LICENSE](LICENSE)

---

## Related

- [Claude Code](https://claude.ai/claude-code)
- [NotebookLM](https://notebooklm.google.com/) — upload exported chapters here for AI podcast generation
- [uv](https://github.com/astral-sh/uv)
