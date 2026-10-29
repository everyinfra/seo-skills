# 共创：和我们一起做这个 SEO / GEO Skill

[English](CONTRIBUTING.md)

搜索规则每个月都在变，没有哪个团队能从内部看清 18 个市场。在首尔、圣保罗、伊斯坦布尔做 SEO 的人，知道很多英文博客里永远看不到的东西。你清楚某个市场的搜索到底怎么运作，就写进来给更多人用，署你的名字。

大多数贡献不需要写代码。

## 怎么参与

| 你手上有…… | 这样做 |
|---|---|
| 一个想法、一个问题，或者一个你很熟的市场 | 在 [Discussions → Ideas](https://github.com/everyinfra/seo-skills/discussions/categories/ideas) 发帖，或者开一个「提议新市场、打法或能力」的 issue |
| Skill 里有说错或过时的建议 | 开一个「建议有误或过时」的 issue，附带日期的出处 |
| 更好的步骤、检查、模板或示例 | 开一个「改进 Skill」的 issue，或者直接提 PR |
| 一个新市场门户、一套打法或一个脚本 | fork 仓库后提 PR |

不知道从哪开始？看看标了 [`help wanted`](https://github.com/everyinfra/seo-skills/labels/help%20wanted) 和 [`good first issue`](https://github.com/everyinfra/seo-skills/labels/good%20first%20issue) 的 issue。

## 东西放在哪

```text
skills/seo-suite/SKILL.md                     # 入口：先问清需求，再分流
skills/seo-suite/references/markets/<语言>.md  # 每个语言市场一份门户（现有 18 个）
skills/seo-suite/references/<类别>/*.md        # overview / research / content / technical / monitoring
skills/seo-suite/scripts/*.py                 # 只用 Python 标准库的工具脚本
skills/seo-suite/tests/test_*.py              # 测试；run_tests.py 会自动找到
```

- **新市场：** 照着现有门户（比如 [ko.md](skills/seo-suite/references/markets/ko.md)）的结构写，只写在这个市场才成立的东西：搜索引擎、平台、本地渠道、语言习惯、本地流行的误解。
- **事实要有出处。** 每个数字、份额、阈值、规则都附出处链接和你核对的日期。搜索变化快，没有日期的说法没法维护。
- **脚本**只用 Python 标准库，并在 `skills/seo-suite/tests/` 里带一个测试。

## 几条规矩

- **不放密钥。** 不提交 API Key、令牌、密码、Cookie，用 `YOUR_API_KEY` 这样的占位符。
- **不放客户数据。** 不放真实客户网站的私有数据、Search Console 导出或统计数据。
- **用自己的话写。** 不粘贴书、课程、付费工具里的原文；需要的话概括并给链接。
- **默认白帽。** 灰帽手法只能用来讲风险，和现有资料的写法一样。
- **许可。** 本 Skill 用 [Apache-2.0](LICENSE)。提交 PR 即表示你同意你的贡献也按 Apache-2.0 授权（第 5 条）。

## 提 PR 之前

在仓库根目录跑（只需要 Python 3）：

```bash
python3 .github/scripts/check_contribution.py
python3 skills/seo-suite/tests/run_tests.py
```

第一条检查 manifest、元信息，以及你改动的文件里的链接、JSON 和密钥；第二条跑测试（大约一分钟）。把它们列出的问题改掉，再按 PR 模板填写。

## 我们怎么审

- 维护者定期手动看 issue 和 PR，不会自动合并。
- 我们可能会请你补出处、改一改，或者建议换个写法。这很正常，不代表不收。
- PR 合并后，你的名字会加进 [CONTRIBUTORS.md](CONTRIBUTORS.md)。我们也在给 [everyinfra.com](https://everyinfra.com) 加贡献者展示。

关于共创的问题，到 [Discussions](https://github.com/everyinfra/seo-skills/discussions) 来问。
