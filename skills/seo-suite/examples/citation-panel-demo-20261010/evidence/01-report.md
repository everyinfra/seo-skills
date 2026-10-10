== AI 可见性面板报告: Nimbus Analytics ==
prompts=6 runs=6 cells=36 engines=chatgpt,perplexity
-- 五状态分类 --
  no_answer             2  (  5.6%)  ← 留在覆盖分母,计 zero-presence
  failed                1  (  2.8%)  ← 采集失败≠内容缺口,不入分母
  brand_absent         12  ( 33.3%)
  name_only_mention     5  ( 13.9%)
  cited_brand          16  ( 44.4%)
-- mention coverage --
  Σmentioned=21 / 成功 cell=35(=cells−failed;no_answer 计 0 留分母)= 60.0%
-- citation share(每答案每品牌至多计 1 次,各品牌恒和 100%)--
  nimbus.example: 16 / 36 = 44.4%
  同场竞品域(top5): rival.example 19.4%, dataschool.io 16.7%, growthnotes.dev 11.1%, devops.to 8.3%
-- 每 prompt 稳定性(≥3 次有效采样才报;z=1.96) --
  best product analytics tools for SaaS    n=6 k=6 p=1.00 CI95[1.00,1.00] stable
  cheapest alternative to enterprise analy n=6 k=2 p=0.33 CI95[0.00,0.71] UNSTABLE(区间跨 0.5)
  how to reduce SaaS churn with cohort ana n=6 k=2 p=0.33 CI95[0.00,0.71] UNSTABLE(区间跨 0.5)
  open source product analytics options    n=5 k=0 p=0.00 CI95[0.00,0.00] stable
  product analytics tools pricing comparis n=6 k=5 p=0.83 CI95[0.54,1.00] stable
  top tools for funnel analysis            n=6 k=6 p=1.00 CI95[1.00,1.00] stable
  [i] 单次引用检查 = 掷硬币:不足 3 次采样的 prompt 不下结论
-- 指标族(Peec 官方公式) --
  SoV = 自身提及/(全部追踪品牌提及) = 16/23 = 69.6%
    (提及以引用域命中为代理——record 未存竞品文本提及;竞品=rival.example)
  win_rate = 排第一次数/响应数 = 3/16 = 18.8%
  citation_rate = 被检索时显式引用均次 = 36/33 = 1.09 次/响应
  brand_visibility(被提)= 60.0% vs source_visibility(被引)= 48.5%(差距 11.5pp)
-- 分引擎(报告按 AI 引擎分列,不合并统计) --
  chatgpt      cells=18  coverage=58.8%   share=44.4%
  perplexity   cells=18  coverage=61.1%   share=44.4%
[!] prompts=6 <10:样本太小,结论只能当方向
