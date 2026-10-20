# 评分器校准方法论(预注册闸门/官方锚点/防泄漏评测/版本化重算)

## 用途与何时读

套件里任何打分脚本(geo_difficulty.py、quality_rater.py、trust_signals.py、serp_occupancy.py 等)要**新建评分、调权重、改阈值曲线**时先读本文。一条铁律先行:权重和曲线**不许手调**——来源仓在权重表上方留了原话注释 `NEVER hand-tune these: refit with the study command under its pre-registered gates`。方法源自 ASO 域(respectlytics/respectaso,App Store 关键词评分器),与域无关,逐条移植到 SEO/GEO。

## 先说清楚:哪些是来源仓的数,哪些是本套件的

- 下文的闸门数值(Spearman ≥0.25、留出 30%、观测 <500 拒绝拟合、每箱 ≥25 观测、尾部上限 250)和结果数字(Spearman 0.61、Pearson 0.65、MAE 8.6、327 个官方值 + 90 个负样本)是 respectaso(App Store 关键词评分器)的值。2026-10-21 重新打开该仓 `rank_calibration_study.py`、`scoring.py`、`services.py`、`popularity.py`、`keyword_scoring.py` 逐条核对,数字与注释一致。
- **它们是 ASO 的,不是 SEO 的。** 本套件至今没有任何评分脚本做过校准:`grep -ln "NEVER hand-tune" scripts/*.py` 无结果。`geo_difficulty.py` 的 0.35/0.40/0.25、`health_score.py` 的类权重、`gsc_mining.py` 的期望 CTR 曲线,都是**本套件口径**。
- 把方法用到 SEO 评分时,阈值要自己在见数据前写下来(第二节),不能直接套 0.25。

## 核心立场

评分器要回答一个它自己看不见的问题(ASO 例:"给定强度的 app 在给定难度的关键词上落在第几名")。答案不许假设,**问平台本身**:每个 SERP 一次就回答 200 个候选的排序问题,一次搜索就是 200 条标注。SEO/GEO 等价物:一份真实 SERP/AI 回答的引用列表就是一次多目标观测。

## 一、官方数据锚点法:任何评分先找绝对锚

相对分数(0-100 自造刻度)没有意义,除非钉在官方绝对值上:

- **找平台的硬锚**:Apple 只上报周搜 ≥~500(~70/天)的词,官方数据集观测地板在 popularity 40——"Apple 有史以来第一个硬绝对锚点",据此整条 POP_TO_SEARCHES 曲线从 pop 40≈70/天 对数线性(~15%/点)外推,斜率再用类目内排名数据(Zipf 500 档 ≈320 倍)交叉核对。
- **拟合目标本身是官方值**:热度估计器 v2 权重 = 327 个官方 searchPopularity(1-100)值 + 90 个 below-top-terms 负样本拟合,holdout 上 Spearman 0.61/Pearson 0.65/MAE 8.6(手调旧权重 Spearman 仅 0.09)。
- **刻度要能一句话说出**:机会分 0-100 = "每天 1 次转化记 50 分,每 10 倍移 20 分"——锚定可解释,而非任意归一。
- **SEO/GEO 等价锚**:GSC 实测点击/曝光(引擎给的一手数)、官方文档明示阈值(如 QRG 档位)、量级类外部锚(已知站点已知词的公开流量)。"评分找不到任何官方绝对锚"本身要写进方法注记,输出降级为纯启发式声明。

## 二、预注册闸门:见数前把判据写死

研究命令的 docstring 里明写:拟合 70%、评测 30%,**对照 docs 计划文档中见任何数据前就固定的闸门**:

| 闸门 | 判据(全部 held-out) |
|---|---|
| R1 | Spearman(预测, 实测) ≥ 0.25 **且高于现行模型** |
| R2 | median abs(log2 预测 − log2 实测) 低于现行模型 |
| E1 | Spearman ≥ 0.25 |
| E2 | 5 个 gap 组的 median abs(log2 均值比) < 0.5 且低于现行模型 |

要点:**闸门必须含"超旧模型"**,不是只过绝对线——旧手调曲线留在研究文件里当 baseline(`_previous_rank`,注明 "set by hand, never measured"),新拟合赢不过它就不许上。**研究命令对产品只读**:打印拟合表与 PASS/FAIL,落地是另行的手工代码变更,测与产分离。首轮 R1 失败的处置也是方法论:分析为什么(plan D3c),提出新模型(期望点击率而非中位排名),新模型按**它自己的**预注册闸门(E1/E2)重判。

## 三、holdout 切分:crc32 哈希按组防泄漏

```python
def held_out(term):
    return (zlib.crc32(f"{seed}:{term}".encode()) % 1000) / 1000 < 0.30
```

- **按 term 切,不按行切**:同一关键词的全部观测行必须进同一侧,否则同词多行分居训练/测试即泄漏。SEO 等价:按关键词或按站点切,绝不按单条结果行切。
- 确定性哈希而非随机抽样:可复现,换 seed 可做多种子稳定性对比(`--summary-json` 逐 seed 追加 E1/E2 值)。
- **原始观测缓存**(`--cache`):refit 永不重新抓取,既省钱又保证同数据重判。
- **拒绝拟合下限**:观测 <500 直接 raise,不输出任何拟合。
- 采样设计:按热度分桶(40-100 八桶)分层抽 + 合成长尾负样本(短词+修饰后缀,确保覆盖官方不上报的区域)。

## 四、三指标:序、线性、倍数误差缺一不可

- **Spearman**(序一致):用户看到的是排序,这是第一闸门;
- **Pearson**(线性):校验刻度本身没有系统性弯曲;
- **MAE / median abs(log2 误差)**:量、排名、流量类是倍数刻度,log2 下对称(差 2 倍 = 1.0);
- 校准专项:按预测难度分 5 组,组内 median abs(log2 均值预测 / 均值实测)——量级对不对,与序对不对分开判。
- 汇总输出永远并列打印 baseline(现行模型、手调曲线、单一信号)供对照,"information only" 标注不参与闸门。

## 五、保序回归(pool-adjacent-violators)拟合单调曲线

散点必然有噪声,但业务约束是单调的("更难的关键词绝不更容易"):

1. 按 gap 分箱(5 分一箱,每箱 ≥25 观测,不足并入逻辑);
2. 每箱取 **median log-rank**(log 域中位数抗离群);
3. **加权 PAV 合并违规箱**:相邻箱逆序则按箱容量加权平均成块,循环到全程单调;
4. 结点间 log-linear 插值;**首结点前持平**(没有比实测最强者更好的),**末结点后按末段斜率延伸到硬上限**(cap=250,理由:持平会讨好最难的关键词);
5. **期望值与典型值两张表**:评分用有效排名(点击率期望的等价排名——计的是概率加权的收获);屏幕给人看中位数落点与 top-10 占比——"平均数当承诺几乎无人兑现"是谎言,两个受众两张表,同一数据。

SEO/GEO 移植:难度分对 SERP 强度、GEO 分对引用份额、审计 confidence 对人判,都适用"分箱中位数 + 加权保序 + 结点插值 + 单调强制"。

## 六、版本化重算纪律:三个版本号独立 bump

```python
ESTIMATOR_VERSION = 2      # 权重/拟合变了
CLASSIFICATION_VERSION = 9 # 标签规则变了(同一分数,不同叫法)
DIFFICULTY_VERSION = 3     # 难度算法变了
```

- **独立 bump,各管各的**:只有对应逻辑变化才 bump 对应号;bump 才触发一次性历史重算;不 bump 则屏上一直显示旧答案——这是显式契约,不是遗忘。
- **重算用冻结输入**:存档时的竞品快照原样保留,"观测到什么还是什么,变的只是算法";重算失败记 error 不阻断启动。
- **特征提取器单一来源**:研究命令用的特征函数就是线上评分用的同一个(`signal_components`),注释原话 "the fitted weights and the shipped code can never drift apart"。SEO 套件等价:校准脚本 import 打分脚本的特征函数,绝不复写一份。
- 平滑信号设计(拟合前置条件):位置加权份额替代 top-N max——一个成员挪一位,特征只动自己的那份,**绝不该从 0 翻到 1**(top-5 最大值就有这个病)。

## 七、twin-row 一致性:一次测量,处处同值

同一关键词×同一店面×不同 app = twin 行。**属于搜索的字段(热度、难度、竞品)不属于 app**,twin 行在这些字段上必须永远一致;真实事故:同日两行显示 52 与 53(各自时刻各自读的)。机制:

- 一次读数(`store_read`)在**一个事务里**深拷贝写入本行与全部 twin 行,各 twin 只保留自己的排名;
- 启动时跑幂等对齐(`align_twin_history`):把同日 twin 行对齐到当日最新读,已一致则零改动;
- 展示层从存档行渲染(`result_payload`),与实时算逐字段一致——数小时前的结果卡和刚跑的显示相同。

SEO/GEO 移植:同一 URL 出现在多个报告/实体/扫描里时,审计结论、覆盖率、E-E-A-T 判定字段一律"读一次、写全部、各自只留自己的位置型字段";禁止每个消费者各自测量。

## 检查清单(新评分器上线前逐项过)

| # | 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|---|
| 1 | 有官方绝对锚,或声明为纯启发式 | 在脚本头注释写出锚的来源 URL;没有就写「纯启发式,未校准」 | 头注释有来源或有声明 |
| 2 | 判据在见数前写进计划文档并注明日期,含「超旧模型」条款 | 计划文档的提交时间早于第一次跑数据的时间(`git log --format=%cI -- <文档>`) | 提交早于数据:通过 |
| 3 | 校准数据缓存落盘,观测不足时拒绝拟合 | 脚本有 `--cache` 一类参数;观测数低于下限时报错退出 | 低于下限的输入被拒绝 |
| 4 | 留出集按键哈希切分,同键同侧 | 运行下面的 Python 片段,同一键两次结果相同 | 两次相同:通过 |
| 5 | 三指标并列输出,并与 baseline 对照 | 输出同时含 Spearman、Pearson、log2 误差和现行模型的同一组数 | 缺任一项:失败 |
| 6 | 单调关系用加权 PAV 强制 | 输出的曲线随难度单调不降 | 出现反向区间:失败 |
| 7 | 权重表上方留「NEVER hand-tune」注释,指向重拟合命令 | `grep -n "NEVER hand-tune" <脚本>` | 有命中:通过 |
| 8 | 每类逻辑一个独立版本号 | `grep -n "_VERSION *=" <脚本>`,改权重时只 bump 对应号 | 版本号随改动变化 |
| 9 | 校准脚本与线上代码共用同一特征提取器 | 校准脚本里 `import` 打分脚本的函数,不复写 | 没有第二份实现 |
| 10 | 一次测量扇出写全 | 同一对象出现在多个报告里,字段值一致 | 无字段分歧 |

可直接运行的最小工具(标准库,按键哈希切留出集 + Spearman):

```python
import zlib, math

def held_out(key, seed="s1", share=0.30):
    return (zlib.crc32(f"{seed}:{key}".encode()) % 1000) / 1000 < share

def rank(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):                      # 并列取平均名次
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r

def spearman(a, b):
    ra, rb = rank(a), rank(b)
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
    return num / den

print(spearman([1, 2, 3, 4, 5], [2, 4, 6, 8, 10]))   # 1.0
print(spearman([1, 2, 3, 4, 5], [5, 4, 3, 2, 1]))    # -1.0
print(held_out("kw-a") == held_out("kw-a"))           # True:同一键永远同侧
```

现有脚本的自检:`python3 scripts/geo_difficulty.py --self-test`(只验证算术,不验证权重是否合理)。

## 来源

- 一手深读(2026-10-09,depth-1 克隆):[respectlytics/respectaso](https://github.com/respectlytics/respectaso) `aso/management/commands/rank_calibration_study.py`(469 行,全部闸门/PAV/crc32 实现)、`aso/scoring.py`(POP_TO_SEARCHES 锚定、RANK_BY_GAP/TYPICAL_BY_GAP 双表、rank_from_gap 外推)、`aso/services.py`(PopularityEstimator.V2_WEIGHTS 与 NEVER hand-tune 注释、信号设计)、`aso/popularity.py`(三版本号与重算)、`aso/keyword_scoring.py`(twin 行读写与对齐)。
- 本文为方法论提炼,数字均出自上述文件内注释(2026-10-21 重新核对,一致);引用实现细节以仓库原文件为准。
