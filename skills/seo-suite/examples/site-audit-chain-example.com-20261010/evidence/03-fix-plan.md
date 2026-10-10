# SEO Fix Plan — https://example.com

- 审计来源: 审计文件(--audit) · verdict: **fail** · findings 16 条 · AI Search Health **70/100**
- 模式: **dry-run**(默认只打印;`--apply` 才写盘,且只写 `./seo-fixes/`)

## [1] robots — create

robots.txt 缺失 → 27 bot 三层模板(引用 5 bot 专属规则).

目标文件: `seo-fixes/robots.txt`

    # robots.txt 全量模板(fix_plan.py 生成——审计发现 /robots.txt 不可达,按缺失处理)。
    # 三层名单与三行格式复用 robots_posture.py(27 bot = training 12/search 10/user 5);
    # 引用 5 bot(OAI-SearchBot/Claude-SearchBot/PerplexityBot/Googlebot/Applebot)已有专属规则;
    # training 层是授权决策——不想喂训练可整组删除,不影响搜索可见性。
    Sitemap: https://example.com/sitemap.xml
    # —— 引用层(search):被封/缺失=逐出 AI 答案,建议追加 ——
    # OpenAI ChatGPT 搜索索引(AI 引用入口)
    User-agent: OAI-SearchBot
    Allow: /

    # Anthropic Claude 搜索索引(AI 引用入口)
    User-agent: Claude-SearchBot
    Allow: /

    # Perplexity 搜索/引用(不训练)
    User-agent: PerplexityBot
    Allow: /

    # Google 通用收录+AI Overviews
    User-agent: Googlebot
    Allow: /

    # Apple Siri/Spotlight 收录
    User-agent: Applebot
    Allow: /

    # Bing 收录(喂 Copilot,无独立 Copilot bot)
    User-agent: Bingbot
    Allow: /

    ... (85 remaining lines)


## [2] llms — create

/llms.txt 缺失 → llms.txt 骨架(H1+blockquote 摘要+## Pages).

目标文件: `seo-fixes/llms.txt`

    # Example Domain

    > YOUR_SITE_DESCRIPTION

    ## Pages

    - [YOUR_PAGE_NAME_1](https://example.com/YOUR_PAGE_PATH_1): YOUR_PAGE_DESCRIPTION
    - [YOUR_PAGE_NAME_2](https://example.com/YOUR_PAGE_PATH_2): YOUR_PAGE_DESCRIPTION
    - [YOUR_PAGE_NAME_3](https://example.com/YOUR_PAGE_PATH_3): YOUR_PAGE_DESCRIPTION

    <!-- 骨架由 fix_plan.py 生成(llmstxt.py generate 同构;3 条占位(审计未见 sitemap URL))——上线前补每条冒号后的说明,并用 llmstxt.py validate 校验 -->


## [3] schema — snippet

无 JSON-LD → WebSite+Organization 片段(FAQPage 已退役,不生成).

目标文件: `seo-fixes/schema-jsonld.html`

    <!-- JSON-LD 片段:粘贴到全站 <head>(审计:无 JSON-LD/缺基础实体)。只补 WebSite+Organization;FAQPage 不生成:Google FAQ 富结果 2026-05-07 全站退役(borrow-specs E5 过时信号表;存量保留勿新增,真实问答内容用 QAPage) -->
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "WebSite",
      "name": "Example Domain",
      "url": "https://example.com"
    }
    </script>
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "Organization",
      "name": "Example Domain",
      "url": "https://example.com",
      "logo": "https://example.com/YOUR_LOGO_URL",
      "sameAs": [
        "https://YOUR_SOCIAL_PROFILE"
      ]
    }
    </script>


## [4] meta — snippet

meta 缺失 5 项(description, canonical, og:title, og:description, og:image) → 补全片段.

目标文件: `seo-fixes/meta-tags.html`

    <!-- meta 补全片段:只含缺失的 5 项(description, canonical, og:title, og:description, og:image);值取页面现有内容或 YOUR_* 占位符,已全部 html.escape -->
    <meta name="description" content="YOUR_DESCRIPTION">
    <link rel="canonical" href="https://example.com">
    <meta property="og:title" content="Example Domain">
    <meta property="og:description" content="YOUR_DESCRIPTION">
    <meta property="og:image" content="https://example.com/YOUR_OG_IMAGE.png">


## [5] content — create

内容信号弱(1 条审计依据) → content-rewrite.md 提纲.

目标文件: `seo-fixes/content-rewrite.md`

    # 内容重写提纲:Example Domain

    > fix_plan.py 只生成提纲,不做自动重写——人工扩写/改写后重跑 site_audit 验证。

    ## 审计依据(内容信号弱)

    - [WARN] content: 词数 27 <200(soft-thin)

    ## 重写目标

    - 词数:当前 27(soft-thin <200 需扩写;>15000 需拆分成块,AI 上下文过载)
    - 首段直答(BLUF):前 100 词内先给答案与事实锚点(AI 引用 38-40% 来自前 100 词,borrow-specs C1)
    - 分块:段落独立可解(non-chunked 修复),H1 唯一且 H2>=2

    ## 建议结构(骨架)

    ## <直接回答:一句话核心事实+适用条件>

    ## <展开:机制/步骤/数据>

    ## <常见问题>(真问答用 QAPage;FAQPage 富结果 2026-05 已退役)

    ## 完成检查清单

    - [ ] 首段 100 词内含直接答案
    - [ ] H1 唯一、H2>=2、段落均长 50-200 字符
    - [ ] 重跑 python3 scripts/site_audit.py 验证词数与 BLUF 检查


**收益预估**: 修复前 70/100 → 修复后预估 100/100 (+30;llms:+15, schema:+15;类别满分取 ai_search_health 权重,封顶 100)

