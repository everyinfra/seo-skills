#!/usr/bin/env python3
"""B60 回归(S4,2026-10-21):directory_tracker.py verify 认全 Google 的三个链接限定属性
(https://developers.google.com/search/docs/crawling-indexing/qualify-outbound-links):
rel="sponsored" / "ugc" / "nofollow" 都让链接不再是 dofollow,分别报出;rel 多值按空白拆分。
修前:只认 nofollow,rel="sponsored"/"ugc" 被当成 dofollow 盖 verified 章(退出码 0)。
合成数据、打桩 fetch、零网络。"""
import contextlib
import io
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from test_directory_tracker import DirectoryCase, TARGET  # noqa: E402


def page(rel):
    attr = (' rel="%s"' % rel) if rel is not None else ""
    return '<html><body><a%s href="https://acme.com/x">Acme</a></body></html>' % attr


class RelQualifierTests(DirectoryCase):
    def verify_json(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = self.dt.cmd_verify(["--entry", "DIR-001", "--target", TARGET, "--json",
                                     "--file", os.path.join(self.tmp,
                                                            "directory-submissions.csv")])
        return rc, json.loads(buf.getvalue())

    def test_check_dofollow_each_qualifier(self):
        cases = {
            None: (True, "dofollow"),
            "noopener noreferrer": (True, "dofollow"),
            "sponsored": (True, "sponsored"),
            "ugc": (True, "ugc"),
            "nofollow": (True, "nofollow"),
            "nofollow noopener": (True, "nofollow"),
            "UGC\tnoopener": (True, "ugc"),
        }
        for rel, want in cases.items():
            with self.subTest(rel=rel):
                self.assertEqual(self.dt.check_dofollow(page(rel), TARGET)[:2], want)

    def test_rel_qualifiers_listed(self):
        self.assertEqual(self.dt.rel_qualifiers(page("sponsored ugc noopener"), TARGET),
                         ["sponsored", "ugc"])
        self.assertEqual(self.dt.rel_qualifiers(page("noopener"), TARGET), [])

    def test_verify_sponsored_not_verified(self):
        self.add_listing()
        self.stub(body=page("sponsored noopener"))
        rc, payload = self.verify_json()
        self.assertEqual(rc, 1)
        self.assertEqual(payload["result"], "sponsored_found")
        self.assertEqual(payload["checks"]["dofollow"], "sponsored")
        self.assertEqual(payload["checks"]["rel_qualifiers"], ["sponsored"])
        row = self.store()[0]
        self.assertEqual((row["Status"], row["Dofollow"]), ("live", "sponsored"))

    def test_verify_ugc_not_verified(self):
        self.add_listing()
        self.stub(body=page("ugc"))
        rc, payload = self.verify_json()
        self.assertEqual(rc, 1)
        self.assertEqual(payload["result"], "ugc_found")
        self.assertEqual(self.store()[0]["Dofollow"], "ugc")


if __name__ == "__main__":
    unittest.main()
