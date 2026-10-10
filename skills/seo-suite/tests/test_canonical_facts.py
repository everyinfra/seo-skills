#!/usr/bin/env python3
"""已知错误陈述回归测试(过时信号看门,E5 口径)。

扫描 skills/seo-suite/{SKILL.md, references/**, templates/**} 的全部 .md 文本,
命中 WRONG_STATEMENTS 中任一正则即 fail,并逐条打印 文件:行号:匹配串。
权威口径表:references/technical/deprecated-signals.md(时间戳与一手来源以该表为准;
本表头亦规定:文档与其冲突时改文档并跑本测试)。

standalone、零网络:`python3 tests/test_canonical_facts.py` 单跑;
亦被 tests/run_tests.py 自动发现(本文件勿做 import 期副作用)。

正则设计契约:既要命中中文/英文的典型错误表述,又必须放过套件内既有正确表述
(如"FID 已被 INP 替代"、"多数 AI 爬虫不执行 JS"、"Page Experience 报告已于
2024-11-18 移除")。SELF_CHECK 把契约钉死:每条正则必须命中全部 bad 样例、
不命中任何 ok 样例——防正则腐烂成摆设,也防其变成误伤器。按行扫描,跨行句式
不在本测试能力内(与 lint 同口径)。
"""
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SUITE_ROOT = os.path.dirname(HERE)  # .../skills/seo-suite
SCAN_ROOTS = [os.path.join(SUITE_ROOT, p) for p in ("SKILL.md", "references", "templates")]


# ---------------------------------------------------------------- 正则常量 --
PAT_FID = (r"(optimize|improve|reduce|monitor|fix|target) (your )?FID\b"
           r"|FID (score|metric|target|threshold)"
           r"|(优化|改善|降低|提升|监测) ?FID"
           r"|FID[^。\n]{0,15}(?<![不再是])(是|属于)[^。\n]{0,15}(核心|关键)?[^。\n]{0,8}"
           r"(指标|信号|[Vv]ital|metric|signal)"
           r"|First Input Delay[^。\n.]{0,40}(metric|vital|target|KPI)")

PAT_FAQPAGE = (r"(新增|添加|部署|加上|上线|标记) ?FAQPage[^。\n]{0,50}"
               r"(富结果|rich result|rich snippet|SERP|搜索结果摘要)"
               r"|(add|implement|deploy)[^.\n]{0,25}FAQ ?Page ?(schema|markup|structured data)?"
               r"[^.\n]{0,60}(rich result|rich snippet)")

PAT_HOWTO = (r"(新增|添加|部署|加上|上线|标记) ?HowTo[^。\n]{0,50}(富结果|rich result|rich snippet)"
             r"|HowTo[^。\n]{0,30}(富结果|rich result)[^。\n]{0,20}"
             r"(仍可获得|仍可|还可以|可获得|仍展示|仍会|still (available|shown))")

PAT_FAMILY_2025 = (r"(新增|添加|部署|加上|上线|标记) ?"
                   r"(CourseInfo|Course ?Info|EstimatedSalary|LearningVideo|ClaimReview|"
                   r"VehicleListing|SpecialAnnouncement|Practice ?Problem)[^。\n]{0,60}"
                   r"(富结果|rich result|rich snippet)"
                   r"|(add|implement|deploy)[^.\n]{0,30}(CourseInfo|EstimatedSalary|"
                   r"LearningVideo|ClaimReview|VehicleListing|SpecialAnnouncement|"
                   r"Practice Problem)[^.\n]{0,50}(rich result|rich snippet)")

PAT_CWV2 = (r"(?<!未)(?<!不)(?<!从未)(?<!并不)(推出|发布|上线|宣布|引入|launch(?:ed)?|"
            r"releas(?:e|ed)|roll(?:ed)? out)[^。\n]{0,20}(CWV ?2\.0|CWV2\.0|Core Web Vitals 2)"
            r"|(CWV ?2\.0|CWV2\.0|Core Web Vitals 2)[^。\n]{0,30}"
            r"(已(发布|上线|推出|生效)|正式(发布|上线)|is (here|live|launched))")

PAT_VSI = (r"(?<!无)(?<!无 )(?<!没有 )(?<!非)(VSI|Visual Stability Index|Visual Search Index)"
           r"[^。\n]{0,30}(指标|信号|metric|signal)")

PAT_ENGAGEMENT = (r"(?<!无)(?<!无 )(?<!没有 )(?<!非)"
                  r"(Engagement[ -]?Reliability|互动可靠性|交互可靠性)[^。\n]{0,40}"
                  r"(指标|信号|metric|signal)")

PAT_LCP_2S = (r"(LCP|Largest Contentful Paint)[^。\n]{0,30}(阈值|threshold|门槛)[^。\n]{0,15}"
              r"(?<![未不])降(至|到|为)?[^。\n]{0,8}2(\.0)? ?(s|秒)"
              r"|((?<![未不])降(至|到|为)|收紧到|lowered to|reduced to|tightened to) ?2(\.0)? ?(s|秒)"
              r"|LCP[^.\n]{0,30}(lowered|reduced|tightened|changed)[^.\n]{0,10}to ?2(\.0)?s?")

PAT_PRIORITY = (r"priority[^。\n]{0,25}(?<![未不没无])(影响|决定|提升|提高|增加|改变)[^。\n]{0,25}"
                r"(排名|抓取|收录|权重|频率|优先级|crawl|rank)"
                r"|(提高|调高|设置高)[^。\n]{0,12}priority"
                r"|(sitemap )?priority[^.\n]{0,40}(affects|influences|boosts|improves|controls)"
                r"[^.\n]{0,30}(rank|crawl)")

PAT_CHANGEFREQ = (r"changefreq[^。\n]{0,30}(?<![未不没无])(影响|决定|控制|提高|增加|调节)[^。\n]{0,25}"
                  r"(抓取|爬取|频率|优先|crawl)"
                  r"|changefreq[^.\n]{0,40}(controls|determines|affects|influences)[^.\n]{0,30}crawl")

PAT_AI_JS = (r"(所有|全部)(AI ?爬虫|AI ?机器人)[^。\n]{0,10}不(会|能)?(执行|渲染)"
             r"|(AI ?爬虫|AI ?机器人)[^。\n]{0,10}(都|一律|完全|全部)不(会|能)?(执行|渲染)"
             r"|(all|no) AI (crawlers?|bots?|spiders?)[^.。\n]{0,40}(execute|render|run) ?Java[Ss]cript"
             r"|AI (crawlers?|bots?)[^.。\n]{0,25}never (execute|render)")

PAT_GBP_CHAT = (r"(GBP|Google Business Profile|商家资料)[^。\n.]{0,30}(chat|聊天|call history|通话记录)"
                r"[^。\n.]{0,40}(仍在|还在|可用|仍开放|仍支持|开启|启用|available|still)")

PAT_PR_NEXT = (r"(PageRank|PR ?值|PR值)[^。\n]{0,12}[Nn]ext"
               r"|[Nn]ext[^。\n]{0,10}(PageRank|PR ?值|PR值)"
               r"|(恢复|回归|重启|重新公开)[^。\n]{0,15}(PageRank|PR ?值|PR值|toolbar ?PR)")

PAT_SCULPT = (r"(PageRank|PR|权重|nofollow)[^。\n]{0,25}(sculpting|雕塑|雕刻)"
              r"(?![^。\n]{0,20}(失效|无效|不再|已死|过时|dead|误区))"
              r"|(sculpting|雕塑|雕刻)[^。\n]{0,30}(仍然有效|依然有效|是有效的|可行|still works)")

PAT_INDEXING_API = (r"(Indexing API|IndexingAPI)[^。\n]{0,50}(?<![不非仅只])可?"
                    r"(提交|推送|加速|收录|submit|publish)[^。\n]{0,20}(任意|任何|所有|全部)"
                    r"[^。\n]{0,8}(URL|页面|网页|网址|URLs?|pages?)?"
                    r"|(Indexing API)[^.\n]{0,60}(any|all) (URLs?|pages?)")

PAT_PAGE_EXP = (r"(Page Experience ?报告|Page Experience report)[^。\n.]{0,30}"
                r"(可查看|去查看|仍可用|仍提供|还提供|还在|still available|to view|to check|"
                r"in Search Console)"
                r"|(打开|查看|去看|检查|找到) ?(GSC|Search Console)[^。\n.]{0,30}Page Experience"
                r"|(GSC|Search Console)[^。\n.]{0,20}(查看|打开|去看)[^。\n.]{0,20}Page Experience")


# ------------------------------------------------- (正则, 为何错) 清单本体 --
WRONG_STATEMENTS = [
    (PAT_FID,
     "FID 已于 2024-03-12 被 INP 替代,2024-09-09 起从 CrUX/PSI 字段数据移除;"
     "把 FID 当现行指标优化/监测是过时口径(见 deprecated-signals.md 第二节)"),
    (PAT_FAQPAGE,
     "FAQPage 富结果 2026-05-07 起全站退役:不为 SERP 新增这类标记,"
     "真问答页用 QAPage(处置见 deprecated-signals.md 第一节)"),
    (PAT_HOWTO,
     "HowTo 富结果 2023-09 起 SERP 停展,不再存在'部署 HowTo 拿展示位'的做法"),
    (PAT_FAMILY_2025,
     "Course/EstimatedSalary/LearningVideo/ClaimReview/VehicleListing(2025-06-12)、"
     "SpecialAnnouncement(2025-07)、PracticeProblem(2026-01)均已不再产生富结果,"
     "替代方案见 deprecated-signals.md 替换决策表"),
    (PAT_CWV2,
     "'CWV 2.0' 是第三方幻觉名目,官方从未宣布;现行口径仍是 LCP/INP/CLS(+TTFB 辅助)"),
    (PAT_VSI,
     "'VSI' 指标不存在,系幻觉名目;视觉稳定性的官方指标是 CLS"),
    (PAT_ENGAGEMENT,
     "'Engagement Reliability' 指标不存在,系幻觉名目,勿引用"),
    (PAT_LCP_2S,
     "LCP Good 阈值官方口径仍为 ≤2.5s,从未降至 2.0s/2s"),
    (PAT_PRIORITY,
     "sitemap <priority> 被 Google 忽略,不影响排名也不影响抓取调度;"
     "lastmod(真实)才是被参考的字段"),
    (PAT_CHANGEFREQ,
     "sitemap <changefreq> 被 Google 忽略,不控制抓取频率/优先级;"
     "抓取调度看抓取历史+lastmod+内外链"),
    (PAT_AI_JS,
     "绝对化表述错误:并非所有 AI 爬虫都不执行 JS(Googlebot 渲染并喂 AIO/AI Mode);"
     "套件口径是'多数 AI 爬虫不执行 JS',因此 meta/schema 必须在初始 HTML"),
    (PAT_GBP_CHAT,
     "GBP chat 与 call history 已于 2024-07-31 下线,不存在'仍在/可开启'的说法"),
    (PAT_PR_NEXT,
     "'PageRank Next/PR 值 next 版本'不存在;工具栏 PR 2016 年停更且从未回归,"
     "第三方 0-10 是另一套近似指标"),
    (PAT_SCULPT,
     "PageRank sculpting(noflow 导流/雕塑权重)2009 年起失效:"
     "nofollow 不再把权重导给其余链接,而是直接扣除"),
    (PAT_INDEXING_API,
     "Indexing API 官方仅限 JobPosting 与 BroadcastEvent;"
     "拿它提交任意/全部 URL 无效果且耗配额(200 publish/天)"),
    (PAT_PAGE_EXP,
     "GSC 的 Page Experience 报告已于 2024-11-18 移除;"
     "看页面体验改用 CWV 报告+HTTPS 报告(信号本身仍在)"),
]

# 自检样例(keyed by 正则文本):(必须全部命中的 bad, 必须全部放过的 ok)
SELF_CHECK = {
    PAT_FID: (
        ["优化 FID 可以提升排名", "FID 是核心指标之一", "optimize your FID score",
         "First Input Delay is a key metric"],
        ["FID 已被 INP 替代", "2024-03 INP 替代 FID 后 Google 未再动核心阈值",
         "用 FID 数据判断响应性是误区:FID 只测首次输入延迟",
         "老站 FID 全绿、INP poor 是常态",
         "任何输出中禁止再引用 FID"],
    ),
    PAT_FAQPAGE: (
        ["添加 FAQPage 结构化数据即可获得富结果", "add FAQPage schema to get rich results"],
        ["FAQPage 富结果 2026-05-07 起全站停展", "不要用 FAQPage——FAQ 富结果已停展",
         "不为 SERP 新增 FAQPage 标记", "UGC 问答不要用 FAQPage,走 QAPage"],
    ),
    PAT_HOWTO: (
        ["部署 HowTo schema 争取富结果", "HowTo 富结果仍可获得"],
        ["FAQ / HowTo 富结果均已停止展示", "HowTo 2023-09 移除"],
    ),
    PAT_FAMILY_2025: (
        ["新增 EstimatedSalary 标记以获得富结果", "implement ClaimReview markup for rich results"],
        ["CourseInfo/EstimatedSalary/LearningVideo/ClaimReview/VehicleListing(2025-06 退役)"
         "一律不再推荐",
         "ClaimReview→Article dateline 替代",
         "EstimatedSalary | JobPosting+baseSalary(单职位口径)"],
    ),
    PAT_CWV2: (
        ["Google 已发布 CWV 2.0", "CWV 2.0 已上线"],
        ["无 CWV 2.0/Core Web Vitals 2.0(不存在)", "官方从未宣布 Core Web Vitals 2.0"],
    ),
    PAT_VSI: (
        ["Google 推出 VSI 指标衡量视觉稳定性"],
        ["无 VSI 这一指标名(第三方幻觉)", "VSI(Visual Stability Index)从未存在"],
    ),
    PAT_ENGAGEMENT: (
        ["Engagement Reliability 是新的排名信号"],
        ["无 Engagement Reliability 之说(幻觉名目)"],
    ),
    PAT_LCP_2S: (
        ["LCP 阈值已降至 2.0s", "LCP threshold lowered to 2.0s"],
        ["LCP 未降 2.0s,仍为 2.5s", "LCP Good 阈值未降至 2.0s", "LCP ≤2.5s / INP ≤200ms / CLS ≤0.1"],
    ),
    PAT_PRIORITY: (
        ["调高 sitemap priority 能提升抓取优先级", "sitemap priority affects rankings"],
        ["`priority`/`changefreq` 已被 Google 忽略(Info 级)", "写了不影响排名与抓取调度"],
    ),
    PAT_CHANGEFREQ: (
        ["把 changefreq 设为 daily 可提高抓取频率", "changefreq determines crawl frequency"],
        ["changefreq 已被 Google 忽略", "changefreq:'weekly' 经 SitemapStream 写入 sitemap.xml"],
    ),
    PAT_AI_JS: (
        ["所有 AI 爬虫都不执行 JavaScript", "AI 爬虫都不执行 JS",
         "all AI crawlers never execute JavaScript"],
        ["社交爬虫与多数 AI 爬虫不执行 JS", "AI 爬虫不执行 JS,初始 HTML 里没有就等于没有",
         "GPTBot/ClaudeBot/PerplexityBot 一般不执行 JS", "most AI crawlers don't execute JavaScript"],
    ),
    PAT_GBP_CHAT: (
        ["GBP chat 功能仍在,记得开启", "Google Business Profile chat is still available"],
        ["GBP chat/call history 2024-07-31 退役", "GBP chat 2024-07-31"],
    ),
    PAT_PR_NEXT: (
        ["Google 上线 PageRank Next", "PR 值 next 版本已发布"],
        ["0-10 Open PageRank(第三方指标)", "域名级 PageRank、谐波中心性"],
    ),
    PAT_SCULPT: (
        ["用 nofollow 做 PageRank 雕塑依然有效", "PageRank sculpting still works"],
        ["PageRank sculpting 2009 年起已失效", "给内链加 nofollow 来「分配权重」是误区"],
    ),
    PAT_INDEXING_API: (
        ["用 Indexing API 提交所有新页面", "use the Indexing API to submit any URL"],
        ["Indexing API 仅限 JobPosting 与 BroadcastEvent",
         "Indexing API 提交器规格(goenning,源码级):9 态状态机",
         "Indexing API 200 publish/天"],
    ),
    PAT_PAGE_EXP: (
        ["去 GSC 查看 Page Experience 报告", "Page Experience report is still available"],
        ["Page Experience 报告已于 2024-11-18 移除",
         "GSC 的 Page Experience 报告已于 2024-11-18 移除(汇总视图,两者均保留)——信号仍在"],
    ),
}


def _iter_md_files():
    for root in SCAN_ROOTS:
        if os.path.isfile(root):
            yield root
        elif os.path.isdir(root):
            for dirpath, _dirnames, filenames in os.walk(root):
                for fn in sorted(filenames):
                    if fn.endswith(".md"):
                        yield os.path.join(dirpath, fn)


class CanonicalFactsTests(unittest.TestCase):
    """已知错误陈述看门:主扫描 + 正则自检(防摆设/防误伤)+ 扫描范围健全性。"""

    def test_scan_scope_resolves(self):
        """路径守卫:扫描根必须解析出足量 .md,防止路径漂移导致空扫描假绿。"""
        files = list(_iter_md_files())
        self.assertGreaterEqual(len(files), 40,
                                "扫描到的 .md 文件异常偏少(%d),检查 SUITE_ROOT 定位" % len(files))
        self.assertTrue(any(os.sep + "SKILL.md" in f for f in files), "SKILL.md 未入扫描范围")

    def test_no_known_wrong_statements(self):
        """主断言:全部 .md 逐行扫描,命中任一 WRONG_STATEMENTS 正则即 fail。"""
        compiled = [(re.compile(p), why) for p, why in WRONG_STATEMENTS]
        hits = []
        for path in _iter_md_files():
            rel = os.path.relpath(path, SUITE_ROOT)
            with open(path, encoding="utf-8", errors="replace") as f:
                for lineno, line in enumerate(f, 1):
                    for rx, why in compiled:
                        m = rx.search(line)
                        if m:
                            hits.append("%s:%d: %r  <- %s" % (rel, lineno, m.group(0), why))
        if hits:
            self.fail("检出 %d 处已知错误陈述(口径见 references/technical/"
                      "deprecated-signals.md):\n  " % len(hits) + "\n  ".join(hits))

    def test_self_check_patterns_catch_bad_samples(self):
        """每条正则必须命中其全部 bad 样例——防止正则写松后看门失效。"""
        for pat, (bad, _ok) in SELF_CHECK.items():
            rx = re.compile(pat)
            for sample in bad:
                self.assertRegex(sample, rx, "正则未命中错误样例(写得太窄):\n  %r\n  pattern: %s"
                                 % (sample, pat))

    def test_self_check_patterns_spare_ok_samples(self):
        """每条正则必须放过其全部 ok 样例——防止正则误伤套件的正确表述。"""
        for pat, (_bad, ok) in SELF_CHECK.items():
            rx = re.compile(pat)
            for sample in ok:
                self.assertNotRegex(
                    sample, rx,
                    "正则误伤正确表述(写得太宽,见 deprecated-signals.md 口径):\n  %r\n  pattern: %s"
                    % (sample, pat))


if __name__ == "__main__":
    unittest.main(verbosity=1)
