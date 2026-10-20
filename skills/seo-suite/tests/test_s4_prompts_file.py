#!/usr/bin/env python3
"""B58 回归(S4,2026-10-21):citation_panel.py init --prompts-file 喂整份 prompt-bank 形态的
Markdown 时,只取「模板/prompt」列单元格(每张表按自己的表头解析),表头行、persona 前缀表、
fanout 定义表、标题、正文句子、列表条目都不算 prompt;没有带 prompt 列的表时,
按一行一条纯文本读。修前:同结构合成文件被解析出表头 + persona 行 + 正文句子。
夹具为合成数据,结构照 templates/research/prompt-bank.md(两张模板表 + persona 表 + 定义表)。"""
import os
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))
import citation_panel as cp  # noqa: E402

BANK_LIKE = """# Sample prompt bank

Intro paragraph that explains the bank. It is prose, not a prompt.

## 1. Main matrix

| 编号 | 漏斗 | 视角 | 模板(整句) | source-seeking 后缀 |
|---|---|---|---|---|
| A1 | 认知 | 品类 | What are the best widgets in {category}? Include sources. | Include sources |
| C1 | 比较 | 替代 | What are alternatives to {competitor}? Cite your sources. | Cite your sources |
| D1 | 决策 | 价格 | Is {brand} worth the price? According to experts. | According to experts |

Note sentence after the table.

## 2. Risk group

| 编号 | 类型 | 模板(整句) | source-seeking 后缀 |
|---|---|---|---|
| R1 | 投诉 | What are complaints about {brand}? Include sources. | Include sources |

## 3. Persona prefixes

| Persona | 前缀[推断] | 固定后缀(本套件口径) |
|---|---|---|
| CMO | As a CMO planning spend, | Respond with sources first. |
| Founder | As a founder, | Respond with sources first. |

## 5. Definitions

| 类型 | 一句定义 | 示例 |
|---|---|---|
| related | engine asks neighbour questions | "best x" -> "x cost" |

- **Usage**: copy the rows you need into a separate file.
1. Another numbered usage line.
"""

EXPECTED = [
    "What are the best widgets in {category}? Include sources.",
    "What are alternatives to {competitor}? Cite your sources.",
    "Is {brand} worth the price? According to experts.",
    "What are complaints about {brand}? Include sources.",
]


def write(content, suffix=".md"):
    fd, p = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)
    return p


class PromptsFileContract(unittest.TestCase):
    def test_bank_shaped_markdown_only_template_column(self):
        objs = cp.read_prompts_file(write(BANK_LIKE))
        self.assertEqual([o["text"] for o in objs], EXPECTED)
        self.assertEqual([o.get("stage") for o in objs],
                         ["awareness", "consideration", "decision", None])

    def test_plain_text_one_per_line(self):
        objs = cp.read_prompts_file(write("best crm 2026\n- crm pricing\n\n# heading\n",
                                          ".txt"))
        self.assertEqual([o["text"] for o in objs], ["best crm 2026", "crm pricing"])

    def test_real_prompt_bank_yields_22(self):
        """仓里的真模板:主矩阵 20 + 风险组 2 = 22 条(修前 72)。"""
        path = os.path.join(BASE, "templates", "research", "prompt-bank.md")
        objs = cp.read_prompts_file(path)
        self.assertEqual(len(objs), 22)
        self.assertTrue(all("|" not in o["text"] and "模板" not in o["text"] for o in objs))


if __name__ == "__main__":
    unittest.main()
