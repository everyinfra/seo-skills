#!/usr/bin/env python3
"""market_lint 三处误报的回归测试(2026-11-06,everyinfra.com 的 ja/ko 线上页实测)。

期望值来源:翻译会话逐条看过命中原文后的判定(真实页面 /ja/tiktok-api、/ko/tiktok-api):
- 「…であること」是名词化用法,出现在です/ます 体正文里不算常体混用;句末「である。」才算。
- 韩文「좋아요」是「点赞」名词(좋아요 수),不是해요체。
- 同一段内容被渲染多遍(桌面/手机两份)时,「AではなくB」按去重后的句子计。
"""
import os
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import market_lint as ml  # noqa: E402


def lint(market, html):
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "market_lint.py"), "--market", market, f.name],
                       capture_output=True, text=True, encoding="utf-8", env=env)
    os.unlink(f.name)
    return r.stdout + r.stderr


def page(lang, body):
    return '<html lang="%s"><head><title>t</title></head><body><main>%s</main></body></html>' % (lang, body)


class JaKeigoTests(unittest.TestCase):
    def test_nominal_dearu_is_not_plain_style(self):
        body = "<p>音声が認識可能であることを確認します。</p><p>コメントを取得できます。</p>"
        self.assertEqual(ml.r_ja_keigo({"alltext": body})[0], "OK")
        self.assertNotIn("混用", lint("ja", page("ja", body)))

    def test_sentence_final_dearu_still_flagged(self):
        body = "<p>この API は便利である。</p><p>コメントを取得できます。</p>"
        self.assertEqual(ml.r_ja_keigo({"alltext": body})[0], "FAIL")


class JaContrastTests(unittest.TestCase):
    def test_repeated_rendering_counts_once(self):
        para = "全体を網羅するものではなく、公開分だけです。国籍ではなく、表示言語で分けます。"
        text = para * 3
        status, msg = ml.r_ja_ai({"alltext": text})
        self.assertEqual(status, "OK", msg)

    def test_many_distinct_contrasts_still_flagged(self):
        text = "".join("案%dではなく、別案%dです。" % (i, i) for i in range(5))
        self.assertEqual(ml.r_ja_ai({"alltext": text})[0], "FAIL")


class KoRegisterTests(unittest.TestCase):
    def test_like_count_is_not_haeyo(self):
        body = "<p>좋아요 수와 댓글 수를 가져옵니다.</p><p>요청 1,000개당 $0.56입니다.</p>"
        self.assertNotIn("혼용", lint("ko", page("ko", body)))
        self.assertNotIn("混用", lint("ko", page("ko", body)))

    def test_real_haeyo_mix_still_flagged(self):
        body = "<p>댓글을 확인해요. 결과를 정리해요.</p><p>요청당 과금합니다.</p>"
        self.assertIn("混用", lint("ko", page("ko", body)))


if __name__ == "__main__":
    unittest.main()
