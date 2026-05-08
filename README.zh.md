# ebook-to-podcast

一个 Claude Code skill，将电子书（PDF 或 EPUB）按章节拆分，搜索权威书评，并生成结构化中文书评报告——只需一条指令即可完成。

> **开发中。** 章节拆分和书评报告生成功能已完成。原计划包含自动上传到 [NotebookLM](https://notebooklm.google.com/) 生成 AI 播客，但由于非官方 NotebookLM CLI 不稳定，该步骤暂时移除。你仍可以手动将导出的章节文件上传到 NotebookLM。

---

## 功能概览

1. **拆分** — 从 PDF（书签）或 EPUB（目录）中提取章节，每章保存为一个 `.txt` 文件
2. **过滤** — 推荐跳过前言、版权页等 frontmatter/backmatter，并请你确认
3. **翻译** — 对非中文书籍，将章节标题翻译成中文（用于文件命名）
4. **搜索** — 搜索权威媒体、专业书评人以及书中涉及人物的公开评价
5. **报告** — 生成结构化中文书评报告（`书评报告.md`）
6. **导出** — 将筛选后的章节按双语文件名复制到 `chapters/` 文件夹

---

## 环境要求

| 工具 | 用途 |
|---|---|
| [Claude Code](https://claude.ai/claude-code) | 运行 skill |
| [`uv`](https://github.com/astral-sh/uv) | 运行 `split_book.py`（自动管理依赖） |

无需单独安装 Python，`uv` 会自动处理。

---

## 安装

### 方式 A — AI Agent 安装（推荐）

将以下内容粘贴到任意 Claude 会话中：

```
请从 https://github.com/noonsleeping/ebook-to-podcast 安装 ebook-to-podcast skill。
克隆仓库，运行 install.sh，按提示完成配置。
```

Claude 会自动克隆仓库、运行 `install.sh`，并引导你完成路径配置。

### 方式 B — 手动安装

```bash
git clone https://github.com/noonsleeping/ebook-to-podcast.git
cd ebook-to-podcast
bash install.sh
```

安装脚本会询问两个路径：

| 提示 | 默认值 | 说明 |
|---|---|---|
| Inbox 目录 | `~/Downloads/eBooks/inbox` | 放电子书的目录 |
| 输出根目录 | `~/Downloads/eBooks` | 项目文件夹的创建位置 |

安装完成后，skill 文件会复制到 `~/.claude/skills/ebook-to-podcast/`，路径配置写入 `~/.claude/skills/ebook-to-podcast/config.json`。

---

## 使用方法

1. 把 `.pdf` 或 `.epub` 文件放到 inbox 目录
2. 打开 Claude Code，输入：

```
把inbox里的书处理一下
```

Claude 会自动完成所有步骤，每个关键节点都会暂停等待你的确认。

---

## 触发词

以下任意指令均可触发 skill：

- "把 inbox 里的书处理一下"
- "把《xxx》拆分章节"
- "搜一下这本书的评价 / 书评报告"
- "电子书整理 / 建立项目文件夹"
- 把 `.pdf` / `.epub` 放入 inbox 后的任何后续指令

---

## 输出结构

```
~/Downloads/eBooks/<书名>/
├── chapters/               ← 筛选后的章节（.txt），双语文件名
│   ├── Ch01 命运 (Chapter 1 Destiny).txt
│   ├── Ch02 「深刻的哲学问题」 (Chapter 2 "Deep Philosophical Questions").txt
│   └── ...
├── 书评报告.md             ← 结构化中文书评报告
└── .work/
    ├── chapters.json       ← 完整章节清单（含跳过标志、cn_title 等）
    └── chapters/           ← 所有原始章节文件（含跳过章节）
```

---

## 文件命名规则

**非中文书：**

| 类型 | 格式 |
|---|---|
| 有章节编号 | `Ch{NN} {cn_title} ({title}).txt` |
| 无章节编号（Introduction / Epilogue / Preface 等） | `{cn_title}（{title}）.txt` |

**中文书：** `Ch{NN} {title}.txt` / `{title}.txt`

---

## 路线图

- [x] 章节拆分（PDF 书签 + EPUB 目录）
- [x] frontmatter/backmatter 过滤
- [x] 章节标题中文翻译
- [x] 网络书评搜索（媒体 + 书评人 + 相关人士）
- [x] 结构化书评报告
- [ ] NotebookLM 自动上传（受阻：非官方 CLI 不稳定）
- [ ] 音频生成流水线

---

## 许可证

MIT — 详见 [LICENSE](LICENSE)

---

## 相关链接

- [Claude Code](https://claude.ai/claude-code)
- [NotebookLM](https://notebooklm.google.com/) — 将导出章节上传到这里生成 AI 播客
- [uv](https://github.com/astral-sh/uv)
