---
name: ebook-to-podcast
description: 把 inbox 里的电子书（PDF / EPUB）按章节拆分，搜索权威媒体与书评人的评价，生成书评报告，并将筛选后的章节文件存入书目文件夹。必须使用此 skill 当用户说："把这本书处理一下"、"inbox 里的书拆分一下"、"生成书评报告"、"搜一下这本书的评价"，或任何涉及电子书整理 / 书评搜集的请求。也适用于用户把 .pdf 或 .epub 文件放到 inbox 后的任何模糊指令。功能：自动拆分章节 + 过滤 frontmatter/backmatter；非中文书翻译章节名；WebSearch 搜集权威媒体/书评人/相关人士评价；生成结构化中文书评报告；只把用户保留的章节（筛选后）存入输出文件夹。
---

# ebook-to-podcast

把一本电子书按章节拆分 → 筛选章节 → 搜索书评 → 生成评价报告 → 输出整理好的章节文件 + 报告。

## 触发条件

用户说以下任一类型时调用本 skill：
- "把 inbox 里的书处理一下"
- "把《xxx》拆分章节"
- "搜一下这本书的评价 / 书评报告"
- "电子书整理 / 建立项目文件夹"
- "Process the book in my inbox"
- 用户把 `.pdf` / `.epub` 丢进 inbox 后给出的任何后续指令

## 环境约定

路径配置从 `~/.claude/skills/ebook-to-podcast/config.json` 读取：

```json
{
  "inbox_dir": "/path/to/inbox",
  "output_root": "/path/to/output/root"
}
```

如果 `config.json` 不存在，使用默认值：
- `inbox_dir`：`~/Downloads/eBooks/inbox`
- `output_root`：`~/Downloads/eBooks`

其他目录约定：
- **输入目录**：`<inbox_dir>/`（只扫描这里，不递归）
- **输出根目录**：`<output_root>/<书名>/`（每本书一个子文件夹）
- **工作目录**：`<output_root>/<书名>/.work/`（split_book.py 的原始输出，包含所有章节文件 + chapters.json）
- **筛选章节**：只把 `skip_recommended == false` 的章节复制到 `<output_root>/<书名>/chapters/`
- **书评报告**：`<output_root>/<书名>/书评报告.md`
- 依赖：`uv`（需已安装）、WebSearch（联网搜索）

---

## 完整流水（Claude 驱动）

### 步骤 0：读取配置

```bash
cat ~/.claude/skills/ebook-to-podcast/config.json 2>/dev/null
```

读取 `inbox_dir` 和 `output_root`。若文件不存在，使用默认值并告知用户可运行 `install.sh` 完成配置。

### 步骤 1：扫 inbox

```bash
ls -1 <inbox_dir>/*.pdf <inbox_dir>/*.epub 2>/dev/null
```

分三种情况：

- **0 本**：告诉用户 inbox 空，让他丢书进来再调用；结束。
- **1 本**：确认 "找到 X.epub，开始处理"，然后进下一步。
- **≥2 本**：**列清单让用户选哪本**（不自动跑所有）：
  ```
  inbox 里有多本：
  1. book_a.pdf (12.3 MB)
  2. book_b.epub (2.1 MB)
  你想先处理哪本？
  ```

### 步骤 2：拆分章节

```bash
uv run --script ~/.claude/skills/ebook-to-podcast/scripts/split_book.py \
  "<inbox_dir>/<book-file>" \
  "<output_root>/.tmp-work"
```

脚本行为：
- 成功 → stdout 输出 JSON（含 `book_title` / `chapter_count` / `chapter_titles` / `chapters_json` 路径），exit 0
- **exit 3**（无 TOC/目录）→ 告诉用户："这本书没有书签/目录，无法自动拆分。用 Calibre 加目录后重试。" 结束。
- 其他非 0 → 把 stderr 报给用户，结束

**注意**：拆分时先用 `.tmp-work` 临时目录，拿到 `book_title` 后再 mv 到正式目录，避免书名解析错误。

### 步骤 3：准备输出目录

```bash
OUTPUT_DIR="<output_root>/<sanitized-book-title>"
mkdir -p "$OUTPUT_DIR/chapters"
mv "<output_root>/.tmp-work" "$OUTPUT_DIR/.work"
```

书名清洗：去 `\/:"*?<>|` 和前后空白。

### 步骤 4：交互确认（章节过滤 + 章节名翻译）

#### 4a · 章节过滤（按 split_book.py 的 skip_recommended）

读 `chapters.json`，展示章节清单，推荐跳过的标 ⏭️：

```
📖 《<书名>》 共 N 章：
   1. Introduction: Preface (17.9k 字)
⏭️ 2. Also by the Author (111 字 — frontmatter)
   3. Chapter 1: Destiny (36.3k 字)
⏭️ 4. Acknowledgments (7.6k — backmatter)
   ...

推荐：跳过 K 章、保留 M 章。
  • 直接回车 / y → 接受推荐
  • "保留 2,4" → 强制保留
  • "跳过 3,5" → 强制跳过
```

用户调整写回 `chapters.json` 的 `skip_recommended` 字段。

#### 4b · 翻译章节标题（仅非中文书）

判断书名是否含 ≥1 个 CJK 字符 → 中文书则跳过此步。

非中文书：一次性翻译所有 `skip_recommended == false` 章节的 `title` → `cn_title`。

**必读翻译原则**：[`references/translation_principles.md`](references/translation_principles.md)。核心：
1. 现代汉语的雅，不是文言文（禁用"之/乎/以...为度"等虚词）
2. 选词比白话上一档：火花→星火、终结→黄昏、空心化→掏空
3. 保留学术准确 + 反讽引号 + 专有名词音译

翻完把翻译表给用户过目，确认（或修改个别词）后写回 `chapters.json`。

### 步骤 5：搜索书评

用 WebSearch 搜集以下三类来源：

#### 5a · 权威媒体评论

运行 3-5 组搜索（根据书的出版时间调整年份范围）：

```
"{书名}" "{作者}" review
"{书名}" review site:nytimes.com OR site:ft.com OR site:theguardian.com
"{书名}" review site:newyorker.com OR site:theatlantic.com OR site:wsj.com
"{书名}" "{作者}" 书评（中文搜索）
"{书名}" review Pulitzer OR National Book Award（如适用）
```

#### 5b · 书评人 / 专业评价

```
"{书名}" review Goodreads
"{书名}" review Amazon editorial
"{作者}" interview "{书名}"（作者自述）
```

#### 5c · 相关当事人反应

根据书的主题识别关键人物（人物传记 = 书中主角；科技书 = 涉及的公司/人物；历史书 = 后代/相关机构），搜索：

```
"{主角/当事人}" responds "{书名}"
"{主角/当事人}" comments book "{作者}"
"{主角/当事人}" reaction biography
```

**搜索记录**：把有效 URL 和摘要记录在内存中，用于步骤 6。

### 步骤 6：生成书评报告

综合步骤 5 搜到的材料，生成结构化中文报告，保存为 `$OUTPUT_DIR/书评报告.md`。

报告结构：

```markdown
# 《{书名}》书评报告

**作者**：{author}  
**出版**：{publisher}，{year}  
**搜索日期**：{YYYY-MM-DD}

---

## 一、综合评分

{如有 Goodreads / Amazon / 评分网站数据，列出分值与样本量}

## 二、主要媒体评价

### {媒体名称}（{日期}）
{评论要点，不超过 3 句概括，不直接摘录大段原文}

（每家媒体一节）

## 三、书评人亮点观点

{综合多位专业书评人的核心判断：值得读的理由 / 争议点 / 独特视角}

## 四、当事人 / 相关人士反应

{书中主角、涉及人物、机构对本书的公开回应（如有）}

## 五、主题与争议

{评论界重点讨论的主题：作者立场、是否平衡、遗漏的议题等}

## 六、总体印象

{一段综合性结论：这本书适合谁读，在同类作品中的位置}

---

## 参考来源

- [{媒体}]({URL}) — {日期}
- ...
```

**版权合规**：每条引用不得超过 15 个英文单词 / 30 个中文字（fair use 摘引范围）。

### 步骤 7：输出筛选章节

将所有 `skip_recommended == false` 的章节文件，按命名规则重命名后复制到 `$OUTPUT_DIR/chapters/`。

**命名规则**（非中文书）：

有 chapter number（title 含 `Chapter <X>` / `第 N 章` 等）：
```
Ch{NN} {cn_title} ({title}).txt
```

无 chapter number（Introduction / Preface / Epilogue / Foreword 等）：
```
{cn_title}（{title}）.txt
```

中文书（无 cn_title）：
```
Ch{NN} {title}.txt   /   {title}.txt
```

`{NN}` 是从原始 title 提取的两位章节编号（不足补 0）。文件名安全清洗：去 `\/:*?"<>|`，多空白合并为单空格。

复制完后汇报：

```
📁 输出目录：<output_root>/{书名}/
   ├── chapters/  ← M 个筛选章节（.txt）
   └── 书评报告.md

⏭️ 跳过章节（未复制）：K 个（frontmatter / backmatter）
```

---

## 关键规则

1. **幂等**：`chapters/` 已有同名文件则跳过复制；报告已存在则询问用户是否覆盖
2. **单本处理**：inbox 多本时列给用户选，不顺序跑所有
3. **无目录即失败**：PDF 没书签直接报错，不尝试启发式分章
4. **章节过滤**：`skip_recommended=true` 的章节不复制到 `chapters/`，但原始文件保留在 `.work/chapters/`（供用户手动取用）
5. **版权合规**：报告中每处引用不超过 15 英文词 / 30 中文字
6. **搜索失败降级**：某条搜索无结果 → 跳过，不中断；最终报告注明"未找到该来源的评价"
7. **翻译交互确认**：非中文书必须让用户过目翻译表，确认后才写回 chapters.json 并复制章节

---

## 文件引用

- `scripts/split_book.py` — 拆分脚本（PEP 723 inline deps，uv run --script 执行）
- `references/translation_principles.md` — 章节标题中文翻译原则（步骤 4b 必读）

---

## 不做的事

- ❌ 不上传到 NotebookLM（由用户手动完成）
- ❌ 不自动处理 inbox 里的多本书
- ❌ 不自动接受章节过滤推荐——展示给用户确认
- ❌ 不把 EPUB 转成 PDF
- ❌ 不尝试启发式拆分无 TOC 的 PDF
- ❌ 不在报告中大段摘录原文（版权合规）
- ❌ 不自动覆盖已有书评报告——询问用户
