#!/usr/bin/env python3
"""检查跑补跑记下的回归:原话或参数值里的金额被 shell 吃掉时,脚本退出码 2、什么都不写(stdlib unittest,零外网)。

期望值的来源(不从实现反推):
- 补跑转录里的真实输入:被测在双引号里写 `--correct "pricing.model=Single 12 oz bags $18–$26; monthly subscription
  from $22/month; V60 starter kit $45; free US shipping over $40"`,zsh 把 `$18` 这类当成位置参数换成空,脚本收到
  「Single 12 oz bags –; monthly subscription from /month; V60 starter kit ; free US shipping over」,照收、确认,
  把这个错价写进了 .agents/product-marketing.md(v2);被测看到后用单引号重跑,又写一次(v3)。判分要的是一次确认
  一次升版本(v2)、价格是 $22。同一条值在 bash 里会变成「8–6 … from 2/month … kit 5 … over 0」。
- 用户原话(双引号没转义时)在 zsh 里会变成「the subscription is  a month」。
- 修复清单写明的行为:看出金额被吃掉就退出码 2,档案和上下文文件都不动;用单引号重跑的正常值照收,只写一次。
站点、品牌都是合成的。
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import lifecycle as L  # noqa: E402
from test_onboarding_regressions_b5c import Repo, make_site, run  # noqa: E402

QUOTE = ("The site is right: the subscription is $22 a month, the marketing file is out of date there. "
         "Everything else in that file is still right. US only, English. We launched October 18.")
GOOD = "Single 12 oz bags $18–$26; monthly subscription from $22/month; V60 starter kit $45; free US shipping over $40"
ZSH_EATEN = "Single 12 oz bags –; monthly subscription from /month; V60 starter kit ; free US shipping over"
BASH_EATEN = "Single 12 oz bags 8–6; monthly subscription from 2/month; V60 starter kit 5; free US shipping over 0"
ZSH_QUOTE = QUOTE.replace("$22", "")


class ShellEatenTests(unittest.TestCase):
    def setUp(self):
        self.repo = Repo(self, pm_extra="")
        self.repo.start(make_site(self))
        self.pm = os.path.join(self.repo.dir, ".agents", "product-marketing.md")

    def pm_text(self):
        with open(self.pm, encoding="utf-8") as f:
            return f.read()

    def answer(self, value, quote=QUOTE, *extra):
        return self.repo.ob("answer", "--ring", "1", "--set", "profile_ok=都对,收费以站点为准", "--correct",
                            "pricing.model=" + value, *extra, "--quote", quote, "--confirm")

    def assert_refused(self, r, before_pm, before_prof):
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("单引号", r.stderr)
        self.assertEqual(self.pm_text(), before_pm)
        self.assertEqual(self.repo.profile(), before_prof)

    def test_zsh_eaten_value_is_refused_and_nothing_written(self):
        pm, prof = self.pm_text(), self.repo.profile()
        self.assert_refused(self.answer(ZSH_EATEN), pm, prof)

    def test_bash_eaten_value_is_refused(self):
        pm, prof = self.pm_text(), self.repo.profile()
        self.assert_refused(self.answer(BASH_EATEN), pm, prof)

    def test_eaten_quote_is_refused(self):
        pm, prof = self.pm_text(), self.repo.profile()
        self.assert_refused(self.answer(GOOD, ZSH_QUOTE), pm, prof)

    def test_good_value_writes_back_once(self):
        """正常值照收:上下文文件升到 v2、更新记录一条、价格 $22;再确认一次只改语言,文件不再升版本。"""
        r = self.answer(GOOD)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        text = self.pm_text()
        self.assertIn("**Document version:** v2", text)
        self.assertIn("$22/month", text)
        self.assertEqual(text.count("seo-suite onboarding ring 1"), 1)
        r = self.answer(GOOD, QUOTE, "--correct", "market.languages=en")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.pm_text(), text)


class ShellEatenTeachTests(unittest.TestCase):
    def test_teach_rule_with_eaten_quote_is_refused(self):
        repo = Repo(self)
        os.makedirs(repo.ws)
        quote = "Compare pages always show prices like from $19/month".replace("$19", "")
        r = run("teach.py", ["rule", "add", "--quote", quote, "--no-deny", "--ws", repo.ws], repo.dir)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertFalse(os.path.exists(os.path.join(repo.ws, "playbook", "rules.md")))
        r = run("teach.py", ["rule", "add", "--quote", "Compare pages always show prices like from $19/month",
                             "--no-deny", "--ws", repo.ws], repo.dir)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


# 真 shell 的展开结果:每句放进双引号,用 /bin/zsh -f 和 /bin/bash --norc 打印,原样抄下。
# 每行 (原话, zsh 吃掉以后, bash 吃掉以后)。$0 那句取 agent 命令工具(zsh -c)里的实际结果。
SHELL_FORMS = (
    ('The subscription is $22 a month.', 'The subscription is  a month.', 'The subscription is 2 a month.'),
    ('Price is now $25 a month', 'Price is now  a month', 'Price is now 5 a month'),
    ('Plans start at $9/month', 'Plans start at /month', 'Plans start at /month'),
    ('It costs $49 per seat per month', 'It costs  per seat per month', 'It costs 9 per seat per month'),
    ('Single bags $18–$26, subscription from $22/month', 'Single bags –, subscription from /month',
     'Single bags 8–6, subscription from 2/month'),
    ('We charge $5.', 'We charge .', 'We charge .'),
    ('Only $5', 'Only ', 'Only '),
    ('The kit is $45 and shipping is free over $40', 'The kit is  and shipping is free over ',
     'The kit is 5 and shipping is free over 0'),
    ('Pro is $1,299 a year', 'Pro is ,299 a year', 'Pro is ,299 a year'),
    ("It's $9.99/mo", "It's .99/mo", "It's .99/mo"),
    ('Free trial, then $15 a month', 'Free trial, then  a month', 'Free trial, then 5 a month'),
    ('Team plan ($99) and Business plan ($299)', 'Team plan () and Business plan ()', 'Team plan (9) and Business plan (99)'),
    ('$22 a month for the subscription', ' a month for the subscription', '2 a month for the subscription'),
    ('We raised prices to $30', 'We raised prices to ', 'We raised prices to 0'),
    ('between $10 and $20 per user', 'between  and  per user', 'between 0 and 0 per user'),
    ('about $200 per year', 'about  per year', 'about 00 per year'),
    ('US$22 monthly', 'US monthly', 'US2 monthly'),
    ('Annual is $220 ($18.33/month)', 'Annual is  (.33/month)', 'Annual is 20 (8.33/month)'),
    ('Pricing: $19, $49, $99', 'Pricing: , , ', 'Pricing: 9, 9, 9'),
    ('Cheaper than X ($35/mo)', 'Cheaper than X (/mo)', 'Cheaper than X (5/mo)'),
    ('costs $12/user/month', 'costs /user/month', 'costs 2/user/month'),
    ('$5 off the first order', ' off the first order', ' off the first order'),
    ('Each bag is $18', 'Each bag is ', 'Each bag is 8'),
    ('Yes, $22/month is right', 'Yes, /month is right', 'Yes, 2/month is right'),
    ('订阅是每月 $22', '订阅是每月 ', '订阅是每月 2'),
    ('订阅 $22/月,单袋 $18–$26', '订阅 /月,单袋 –', '订阅 2/月,单袋 8–6'),
    ('价格是 $22 一个月', '价格是  一个月', '价格是 2 一个月'),
    ('套餐从 $9 起', '套餐从  起', '套餐从  起'),
    ('团队版 $49/人/月', '团队版 /人/月', '团队版 9/人/月'),
    ('现在涨到 $25 了', '现在涨到  了', '现在涨到 5 了'),
    ('免运费门槛 $40', '免运费门槛 ', '免运费门槛 0'),
    ('年付 $220(约 $18/月)', '年付 (约 /月)', '年付 20(约 8/月)'),
    ('Starts at $0.50 per request', 'Starts at /bin/zsh.50 per request', None),
)
# 只看文字分不出的:zsh 的「US monthly」像一句正常的话;bash 的「(99)」里正好有原话的 99。
ZSH_UNREADABLE = {"US$22 monthly"}
BASH_MONEY_UNREADABLE = {"Team plan ($99) and Business plan ($299)"}
# 容易误判的正常原话:没有金额的数字、用户手滑的双空格、句号后两个空格、法语标点前的空格、「.5」、提到 zsh。
CLEAN = ("2 posts a month is fine", "We publish 4 articles per week", "Pricing is per seat, billed monthly",
         "Hi team,  thanks for this", "Yes. That's right.", "Everything else is right. US only, English.",
         "Use the /pricing page", "We have 3 plans (Free, Team, Business)", "The first 1,000 calls are free",
         "Ratio is .5 on average", "Launch date: Oct 18.", "C'est 22 € par mois ; merci !", "价格以官网为准",
         "订阅 22 美元/月", "每月 22 美元", "都对,收费以站点为准", "Free plan, then 15 EUR a month",
         "costs 22 USD per month", "Yes.  The subscription matters most.", "We use zsh and bash scripts",
         "Free", "Contact sales for annual pricing", "我们的客户是 3 到 15 人的小团队", "Two of us, one post a week.",
         "Corrections:\n  - pricing is right\n  - US only")


class ShellFormsTests(unittest.TestCase):
    def test_zsh_forms_are_flagged_from_the_text_alone(self):
        for orig, zsh, _ in SHELL_FORMS:
            if orig not in ZSH_UNREADABLE:
                self.assertTrue(L.shell_damage(zsh), (orig, zsh))

    def test_bash_forms_of_a_price_value_are_flagged_against_the_quote(self):
        """bash 把 $22 换成「2」,只看文字分不出;价格键的值拿用户原话(写着 $22)对照认得出。"""
        for orig, _, bash in SHELL_FORMS:
            if bash is not None and orig not in BASH_MONEY_UNREADABLE:
                self.assertTrue(L.shell_damage(bash, orig, None, True), (orig, bash))

    def test_clean_text_is_not_flagged(self):
        for s in tuple(row[0] for row in SHELL_FORMS) + CLEAN:
            self.assertEqual(L.shell_damage(s), [], s)
            self.assertEqual(L.shell_damage(s, s, s, True), [], s)


if __name__ == "__main__":
    unittest.main()
