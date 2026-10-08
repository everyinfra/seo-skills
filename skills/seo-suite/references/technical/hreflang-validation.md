# hreflang / 国际化校验（八检框架）

> 建立于 2026-10-09。校验规则参考 [AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo)（MIT）`skills/seo-hreflang/SKILL.md`，按本套件证据约束改写。
> 适用场景：多语言/多区域站。本套件自身即双语（EN/中文），此文件同时服务内部。

## 一、八项校验（每项是真规则，不是清单口号）

| # | 检查 | 规则 | 违例严重度 |
|---|---|---|---|
| 1 | 自引用 | 每个语言版必须含指向自身的 hreflang，且与该页 canonical URL **全等**（含尾斜杠） | Critical——缺失则 Google 可能**忽略整组** |
| 2 | 双向返回 | A→B 则必须 B→A；全网格互指 | Critical |
| 3 | x-default | 仅当回退页真实存在；每组**至多一个** | High |
| 4 | 语言码 | ISO 639-1（`en`/`zh`/`ja`）；拒 `eng`/`jp`。文字用 ISO 15924：`zh-Hant`、`zh-Hans-US` 合法 | High |
| 5 | 区域码 | ISO 3166-1 Alpha-2 **大写**；拒 `en-uk`（应为 `en-GB`）、`EU`/`UN`（非国家）、`es-LA`（非单一国家）；**仅国家码无效**（`-US` 必须配语言） | High |
| 6 | 位置 | hreflang 仅在 canonical URL 上有效；与 canonical 精确匹配（含尾斜杠） | High |
| 7 | 协议 | 组内 https/http 一致 | Medium |
| 8 | 跨域 | 允许，但**两个域都要有返回标签** | High |

## 二、实现方式选择

| 场景 | 推荐 |
|---|---|
| <50 个语言变体 | HTML `<link rel="alternate" hreflang>` 标签 |
| 非 HTML 资源 | HTTP `Link` 头 |
| 50+ 页或跨域 | XML sitemap 内 `xhtml:link` |

## 三、标签之外（常被漏掉的国际化实质）

1. **内容平价字数比**：德语版通常比英语**长 25–35%**、日语**短 10–25%**——大幅偏离提示某语言版是截断/机器直译，不是对等翻译。
2. **本地格式**：`1,000.00` 在 de-DE 应为 `1.000,00`；日期、地址、电话同理。
3. **过期翻译**：EN 改版后其他语言未跟——检测各语言版 dateModified 差距。
4. **未复核机翻**：整站机翻无人工审校标记为 scaled-content-abuse 风险（Google 政策名目）。
5. **文化适配**（软项）：各语言版的示例、案例、货币、合规表述是否本地化，而非字面翻译。

## 四、审计输出格式

每项检查输出：页面 URL 对 / 检查项 / 违例描述 / 严重度 / 修复建议（含正确的标签写法）。整组失效（检查 1/2 违例）时优先提示——单项修好也没用。

## 五、来源

- 八检规则与正反例、严重度表：[AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo) `skills/seo-hreflang/SKILL.md`
- 字数比/本地格式/机翻风险：同上 SKILL.md 的内容平价段
