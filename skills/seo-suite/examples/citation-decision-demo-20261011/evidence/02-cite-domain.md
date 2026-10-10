== CITE 域名评级(结构化输入;Pass10/Partial5/Fail0,unknown 不计均值) ==
[C 引用(.35)] 100.0
  C1   引用域数量                  10      ≥500             | 观测值=950.0
  C2   DR50+ 份额               10      DR50+ ≥20%       | 观测值=0.2631578947368421
  C3   出站链接数                  10      出链<1000          | 观测值=620.0
  C4   链接增速平滑度                10      峰值≤3×月均          | 观测值=1.120331950207469
  C5   跨引擎被引广度                10      ≥2 引擎≥10 查询被引    | 观测值=2
  C6   编辑链占比                  10      编辑链≥60%          | 观测值=0.68
[I 身份(.20)] 100.0
  I1   品牌词行数(reviews)         10      品牌词行 ≥5          | 观测值=7
  I2   品牌词行占比                 10      占比≥50%           | 观测值=0.875
[T 信任(.25)] 100.0
  T1   C-block 集中度            10      ≤20%             | 观测值=0.12
  T2   精确匹配锚文本比               10      精确锚≤30%          | 观测值=0.22
  T3   链接·流量相干性(人工标记)         10      相干               | 观测值=True
  T4   人工处罚记录                 10      无                | 观测值=False
[E 显赫(.20)] 50.0
  E1   跨引擎被引查询总量              5       被引查询 20-50       | 观测值=33.0
  E2   公开评论量                  5       评论 3-10          | 观测值=8
VETO: 无
总分 = 90.0 → band A(优)

-- 引用证据核验(engines_cited=C5/E1 证据口径;5 家 Provider 字段路径) --
  三类来源分离:仅 provider_citation 计入 engines_cited;provider_search_result / answer_text_url 不充数
  openai-chat      choices[0].message.annotations[].url | .url_citation.url
  openai-responses output[i].content[j].annotations[]
  anthropic        content[i].citations[].url
  perplexity       citations[] + search_results[].url
  gemini           candidates[0].groundingMetadata.groundingChunks[].web.uri
