# 视频 SEO/GEO(被 AI 引用的视频层)

> 建立于 2026-10-09。来源:Google/YouTube/Gemini 官方文档为基准;引用占比各家研究差异大(4.4%–29.5%),引用时必须注明样本;标注来源类型(官方/行业/社区)。

## 一、AI 怎么"读"视频(机制)

- **Gemini/AIO「进片内」引用**:指向视频内具体时间戳而非整片;ChatGPT 在视频之间挑选、以整片为单位(行业,BrightEdge)。
- **双通道**:Gemini 直接吃视频 URL 时默认采样 1 FPS 关键帧+音频转写;给 YouTube URL 时按付费层取帧/transcript(官方 API 文档)——**关键帧视觉+transcript 文本是两条被引通道**。
- **ChatGPT 读附着在视频上的"词"**(transcript/标题/描述)而非像素(行业/社区,与 youtube-transcript-api 实践一致)。
- **决定性事实:播放量不是被引门槛,文本可及性才是**——被引视频 41% 播放量不足 1,000,被引与高播放量仅 52% 相关(Gumshoe,行业)。
- **API 可及性(官方)**:captions.download 仅视频所有者可取;第三方视频拿不到官方 transcript——**主动上传的人工校对字幕是唯一可控文本层**。

## 二、YouTube SEO 要素

**官方可见性层**:watch page 可索引;缩略图稳定 URL(≥60×30px);Googlebot 可取视频真实字节(勿 robots 屏蔽 CDN/M3U8);title/description/thumb 各来源一致;视频 sitemap(单文件≤5 万条)加速发现;VideoObject 必须;**Key Moments 两法**——`Clip` 标记(全语言)或 `SeekToAction`(部分语言),YouTube 描述内时间戳亦可。

**算法层(行业,无官方确认)**:CTR(诊断线 ~4%)、前 30 秒留存(目标 80%+)、观看时长。章节(描述时间戳)同时服务站内导航、key moments 与 AI 定位引用。

## 三、视频 GEO 实操清单(8 项)

1. 上传人工校对字幕(transcript 质量直接决定 AI 摘要与引用)。
2. 章节化:描述时间戳+描述性章节名(帮 Gemini 定位"片内某点")。
3. 描述前几行写事实句/可引用定义(数字、结论);标题带目标查询词。
4. 自建 watch page+VideoObject+contentUrl 可爬+视频 sitemap(进 Google 视频索引才可能进 AIO)。
5. `Clip`/`SeekToAction` 显式标 key moments。
6. 口播自然说关键词(ASR 是 YouTube/TikTok/抖音共同索引层);屏幕文字开头叠关键词(OCR 层)。
7. 多市场用 **MLA 多音轨**(官方:单视频多配音+每语言独立标题/描述/缩略图)而非只靠英文字幕;MLA 单频道 vs 分语言频道无定论(行业争议,标注)。
8. 监测:Gumshoe/SE Ranking 类工具查自己视频是否被 AIO 引用;引用≠播放,与品牌监测互补。

## 四、市场差异:视频平台格局

| 市场 | 格局(2026) | 要点 |
|---|---|---|
| 日本 | YouTube 7,850 万用户居首;niconico 边缘化 | AIO 引用榜 YouTube 第 1(套件已录) |
| 韩国 | YouTube 4,813 万、媒体用时 44%;**Naver TV 已于 2026-09-30 关停** | 韩国视频只剩 YouTube 一极 |
| 俄罗斯 | YouTube 降至 6,590 万;**VK Video 与 RuTube 日活已反超** | 俄语视频 GEO 要双投(套件俄语区指南呼应) |
| 中国 | 抖音(标题前 10 字权重最高,社区口径)+B站(关键词+互动+账号权重) | 见中文指南四因子 |
| 全球 | TikTok 关键词三入口:caption/屏幕字(OCR)/口播(ASR);Reels 的 caption 当标题+alt text 可写 | TikTok 自有搜索是 Gen Z 主发现渠道 |

## 五、本地化注意

Google **无视频专有 hreflang 指引**(官方确认的缺口):视频集合页沿用页面级 hreflang;视频地域控制用 `regionsAllowed`/`<video:restriction>`(官方)。

## YouTube 算法与 CTR 硬基准(claude-youtube 精读,百仓深扫)

- **CTR 分流量源**(Focus Digital 2025-12):Search 12.5% / Suggested 9.5% / Browse 3.5% / External 2.8%;档位 <3% 需修 / 4-6 平均 / 7-10 好 / 10+ 卓越;70-100 字符标题比短标题 CTR 高 10-14%,关键词进前 40-50 字符。
- **AVD**:均值 23.7%,仅 16.8% 视频超 50%;**<40% AVD 被降权**;章节 +4% AVD(Backlinko)、留存最高 +50%。
- **三系统独立**(Browse/Search/Shorts)+ **4 层测试级联**(核心观众→扩展→更广→高权威);满意度信号排序:Shares 最强 > repeat viewing > session continuation > saves > surveys > likes > comments。
- 标题 clickbait 惩罚(2024 末起全球):Gemini 对比标题/缩略图与实际内容;tags 已残废(最多 30 秒,只用于错拼消歧);hashtags 3-5 个(>15 全忽略);字幕 +12% 观看时长,手动 SRT 索引优于自动;2 小时内回复 50+ 评论=+15-20% 触达;24h 通知上限 3 次;章节须 0:00 起、≥3 章、每章 ≥10 秒。

## 来源

- 官方:Google 视频 SEO 文档/VideoObject/key moments/视频 sitemap;Gemini API 视频理解;YouTube MLA 帮助页;captions API 文档
- 行业:Suffes Digital(54.9% AIO 含 YouTube 引)、Search Engine Land/BrightEdge(29.5% 第一域名)、Gumshoe(41% 被引视频<1,000 播放)、Contently(transcript 影响)
- 平台口径:2pointagency/Toptal(TikTok/IG)、腾讯云开发者(抖音)、开源中国(B站)、Statista/TechTimes/iz.ru(市场格局)
- GitHub:jdepoix/youtube-transcript-api(8.4k★,免 OAuth 取 transcript 自检)、AgriciDaniel/claude-youtube(436★)、hyperframes-student-kit(1.2k★)
- 本文件由 EveryInfra 编写,仅收录要点与链接

## (claude-youtube 深读 2026-10-09b)余下全量增量:留存/缩略图/Shorts/变现/模板/工具层

> 本轮读完主 SKILL + 14 个 sub-skills + 余下 7 个 references(analytics/monetization/thumbnail-ctr/retention-scripting/shorts/repurposing/dataforseo)+ 3 个模板(education/shorts-first/niche-authority),与前文"精读"节不重复。

### 留存与脚本(retention-scripting-guide)

- **开场流失**:前 60 秒丢 55%、前 10 秒丢 20%;15 秒内给价值主张 = 1 分钟处留存 +18%;10-15 秒留存 <50% 即钩子失败,30 秒 70%/80% 为稳/优。
- **模式打断**:前 5 秒一次 = 留存 +23%;频率按格式——预制 30 秒/次、直播 2-3 分钟/次、Shorts 2-3 秒/次;掉点处打断拉回 15-22%。
- **留存曲线六形态**:悬崖(15 秒内丢 20%+ = 钩子废)、中段谷(40-60% 处 = 节奏)、尖峰(重看段,应主动复制)、悬索桥(开放环)= 完播 +68%、锯齿 = 完播 +43%、平稳下滑 = 正常。
- **算法阈值**:留存高于频道均值 15%+ = 推广量 2.3 倍;留存提升 10 个百分点 = 展示 +25% 以上;**AI 叙事配音留存 -70%**(人出镜为准,除非频道本身 AI 主题)。
- **CTA 布局**:仅 16% 观众看到片尾;1 分钟处约 60% 在看、4 分钟处约 35% → 双 CTA(约 1 分钟 + 约 4 分钟);视觉+口播嵌入式 CTA 比纯口播转化 +380%;有 CTA 每 33 观看 1 订阅(无 CTA 1/83)。
- **长度**:教程 7-15 分钟、娱乐/vlog 8-12、教育 15-25、Shorts 15-30 秒;5-10 分钟留存峰值 31.5%;20+ 分钟视频吃掉全站 57% 观看时长;8 分钟解锁中插(收益约 +50%,勿注水)。
- MrBeast 口径:100 条视频微改进复利(前 ~50 条别指望结果);标题/缩略图的承诺须 5-10 秒内兑现;片尾强 payoff 直接抬 AVD。

### 缩略图与 CTR(thumbnail-ctr-guide)

- 分 niche CTR 基准(Focus Digital 2025-12):游戏 8.5% > 健身 8.0% > 科技评测 7.5% > 美妆 6.5% > 娱乐 6.0% > 财经商科 5.5% > 教育 4.5%(教育最低但搜索意图最强)。
- 人脸缩略图 +20-30% CTR、均多 92.1 万播放;但**中性表情比无脸还差**——要夸张且真实。
- 规格:文字 ≤5 词(理想 3)、2-3 色板、负空间 30-40%、单焦点、<1 秒决策;1280×720 最低 / 1920×1080 供 TV;70%+ 观看在移动端,按 feed 小图检验;信息分工铁律——缩略图管视觉情绪、标题管关键词承诺,**两者文字不得重复**。
- **A/B 测试(Studio 2024 中上线)**:最多 3 版、最长 2 周、仅桌面设置、Shorts/儿童内容不可用;**优化目标是观看时长份额而非 CTR**(低 CTR 版可因观众看得久而赢);百万曝光下 0.5% CTR 差即显著;2024 末新增标题 A/B;案例提升 37-110%。
- 处罚:违规缩略图首犯警告(90 天过期),同期再犯 = strike,3 strike 封频道;色情缩略图**直接封号**无警告。

### Shorts 独立算法体系(shorts-playbook)

- 信号层级:完播/留存(70%+ = 强推)> 循环重播 > 评论分享 > **Viewed vs Swiped Away**(75%+ 良好,<50% 钩子废,**<60% 立即换开场**)> 满意度;CTR 几乎无效;最晚第 4 天才起飞属常态。
- 规格:上限 3 分钟(2024-10)但甜点 15-60 秒、双峰 13 秒/60 秒,**30-45 秒是死区**;视觉每 3 秒一变、钩子 1-3 秒;Content ID 音乐直接封 1-3 分钟 Shorts。
- 计数与新鲜度:2025-03 起任何播放 = 1 观看、循环也计,总量虚高 ~30%,跨期比较用官方 **engagedViews**(2025-04 起正式指标,长视频 = views);2025-09 起 ~28-30 天后降权(长视频常青内容不受影响)。
- 收益:池化分配、创作者留 45%;**音乐按轨分账:无音乐 100%、1 轨 50%、2 轨 33%**;RPM $0.01-0.07(财经至 $0.30);2025 年 Shorts 占 YouTube 广告总收入 22%(2024 为 15%),vidIQ 称 2025 RPM +150%。
- 与长视频:观众重合仅 ~10%、关联视频导流 <1%,但双形态频道增长快 40-60%、美国市场无蚕食(2025-02);**长视频桥接(RPM 为 Shorts 的 10-100 倍)才是 Shorts 频道真正变现路径**;TikTok 水印被降权;Shorts 进 YouTube 搜索 + Google 移动结果(标题 ~40 字符截断、4-6 词、描述前 125 字符承重)。

### 变现数字(monetization-guide + analytics-guide)

- **YPP 两级**:扩展级 500 订 + 90 天 3 更 + (1 年 3K 观看时 或 90 天 3M Shorts 观看)解锁会员/Super/购物;完整级 1K 订 + (4K 时 或 10M Shorts)解锁广告;审核约 1 个月。2025-07 起"重复内容"更名"**不真实内容**"政策——批量模板化/AI 滚雪球内容有掉收益风险。
- RPM/CPM:RPM 恒低于 CPM(已扣 45%);美国观众价值为东南亚 5-8 倍(财经 RPM 美国 $15-25 vs 印度 $0.50-1.50);**Q4 CPM +30-60%、1 月全年最低**;8 分钟+中插使 RPM 约翻倍。分档:财经 $20-40+ / 法务地产 $20-35 / 科技 $15-25 / 教育 $8-15 / 游戏 $2-5(美国中位 $3.50)/ 音乐 $1-3。
- 分成与硬顶:会员 YT 抽 30%($0.99-499.99/月、25 档);Super Chat 70/30、单用户周上限 $2K;购物联盟约 10K+ 订(口径混乱 1K-15K)、佣金 5-20%(中位 ~15%)、单视频 60 商品、30 天归因、2025-06 商品贴纸点击 +40%;商单地板 $1K+(游戏 $0.037/view、生活方式 $0.023);小频道优先商单+外链漏斗而非广告。
- **FTC 披露四件套**:口播(前 15-30 秒)+ 屏幕文字(≥10 秒)+ 描述前两行;**YouTube 付费推广开关单独不合规**;每次违规罚 $53,088 且品牌与创作者连坐;**AI 生成内容需双重披露**。
- Premium:125M+ 订阅、创作者分 ~55%、premium 型频道 15-30% 收入来自此。
- Analytics:CTR 约占初始分发决策的 80%;诊断矩阵——高曝光+低 CTR = 包装问题 / 高 CTR+低 AVD = clickbait / 低曝光+高 CTR = 过窄;CTR 随展示扩张自然下滑(持续 4-8% 即健康);单一流量源 80%+ = 脆弱(analyze 子技能 60% 即报警);Analytics API 单查询 ≤200 行、组 ≤500 视频;Reporting API 数据仅存 60 天、`channel_reach_basic_a1` 含缩略图曝光与 CTR。

### 内容策略与频道模板(repurposing-guide + 3 模板)

- **Hub/Hero/Help**:Hero 1-2 次/年;增长期建议 ~70% Hub / 15% Help / 15% Hero;evergreen:trending = 70-80 : 20-30;**更新旧常青内容流量 +106%**。
- 播放列表是独立 SEO 资产:YouTube+Google 双排名、+40% 观看时长、5-10 条/列表、Series 播放列表强制观看顺序、首条放最强视频;系列 5-7 条为优。
- 微利基:受众缩 5 倍但收入可增("skincare for rosacea"式收窄);扩张三段:1-6 月核心利基 → 7-12 月邻接 → 第二年扩宽。
- **教育频道模板**(留存最高格式 42.1%):Help 60/Hub 30/Hero 10、常青 80%+;月更 12+ = 观看增速 8 倍(vidIQ);双索引面(web Key Moments + YT 搜索)是复利资产。
- **Shorts-first 模板**:流量 ~75% 来自 Shorts feed;solo 日更 1-3 条;系列化格式(Hub 50-60%)让算法识别"连看";断更 2 周 ≈ 清零(28-30 天新鲜窗),需 2 周内容缓冲;5K 订前就得启动长视频桥接,否则"频道大但穷"。
- **利基权威模板**:搜索占 ~40% 流量、CTR 可打 6-9%(展示高度定向);先录 50 个关键词簇再开机;**包装(标题+缩略图)占制作时间 30%**,CTR<4% 时瓶颈在包装不在内容;每订阅收益为娱乐型 5-10 倍。
- 竞对与复用:outlier = 3-10 倍频道均值才入库;评论挖未答问题;一条 20-30 分钟长片 = 10-20 条 Shorts,"钩子-价值弹-CTA"结构比连续切片好 74%;AI 剪辑省 70-90% 工时;vidIQ/TubeBuddy 无公开 API。

### DataForSEO 工具层与 GEO(dataforseo-integration)

- YouTube 端点(~$0.002/次):`serp_youtube_organic_live_advanced`(SERP)、`_video_info_`(元数据/标签/互动)、`_video_comments_`(评论挖掘,免 OAuth)、`_video_subtitles_`(字幕;注意 auto-generation 标志,自动字幕有错)。
- **GEO 检测端点(~$0.01/次)**:`ai_optimization_chat_gpt_scraper`(ChatGPT 引用源)、`ai_opt_llm_ment_search` / `_top_domains`(LLM 提及)——直接查"自己视频是否被 AI 引用",与套件 AIO 引用监测同向,可作工具化路径。
- 方法论:**Google 搜索量 ≠ YouTube 搜索量**(强代理;游戏/教程类在 YT 端偏重);高 Google 量 + informational intent = YT 优选目标;CPC 作 RPM 方向性代理但非线性;Trends 是 0-100 相对指数须配体量;单工作流 $0.004-0.04。
- 主 SKILL 编排:14 子技能路由 + 9 频道类型模板;audit/competitor 各开 4 并行 agent;三道质量门(具体性/数据溯源/完整性)+ self-anneal 回炉;YouTube Data API 日配额 10K 单位、search 每次 100 单位(即日上限 100 次搜索)、太平洋午夜重置。

### 口径矛盾与注意(引用时标注)

- Shopping 联盟门槛官方不清(1K-15K 订各种说法)。
- 标题长度三套口径:playbook 实证 70-100 字符 CTR 更高(已录)vs 教育模板"<55 字符"vs MrBeast"<50 字符"——按流量源取舍(Search 长标题、Browse/MrBeast 式短标题),不是单一答案。
- Shorts 甜点双口径:playbook"15-60 秒"vs 模板"13 秒或 50-60 秒、30-45 死区"——完播最大化取 13s,单次收益最大化取 50-60s。
- "模式打断每 30 秒"偏激进,指南自认 data-supported but aggressive。
