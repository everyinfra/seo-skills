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

## 来源

- 官方:Google 视频 SEO 文档/VideoObject/key moments/视频 sitemap;Gemini API 视频理解;YouTube MLA 帮助页;captions API 文档
- 行业:Suffes Digital(54.9% AIO 含 YouTube 引)、Search Engine Land/BrightEdge(29.5% 第一域名)、Gumshoe(41% 被引视频<1,000 播放)、Contently(transcript 影响)
- 平台口径:2pointagency/Toptal(TikTok/IG)、腾讯云开发者(抖音)、开源中国(B站)、Statista/TechTimes/iz.ru(市场格局)
- GitHub:jdepoix/youtube-transcript-api(8.4k★,免 OAuth 取 transcript 自检)、AgriciDaniel/claude-youtube(436★)、hyperframes-student-kit(1.2k★)
- 本文件由 EveryInfra 编写,仅收录要点与链接
