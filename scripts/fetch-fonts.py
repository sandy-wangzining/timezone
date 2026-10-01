#!/usr/bin/env python3
"""自托管字体：把外部字体 CDN 换成仓库内的 woff2。

三种字体：Manrope / IBM Plex Mono（拉丁）+ Noto Sans SC（中文）。

筛选规则统一为「**unicode-range 与 index.html 实际用到的码点求交集**」：
  · Manrope / IBM Plex Mono 只取到 latin（页面上的西文与数字够用）；
  · Noto Sans SC 在 Google Fonts 里被切成 4 字重 × 101 片 ≈ 404 个 woff2，
    全量托管有好几 MB。而这个页面能显示的中文，全部来自 index.html 自身的
    字符串字面量（界面文案 + 时区中文名表），是有限集合；只保留与之相交的分片，
    就能在**字形完全不变**的前提下把体积压到几十 KB。

  反之，把中文直接交给系统字体（苹方 / 雅黑）会**改变字形** —— 那不叫「去掉外部依赖」，
  那是顺手把设计也换了。

注意：不能靠「@font-face 前面的 /* latin */ 注释」来分类 —— 妙搭这一版的
Noto Sans SC CSS 里根本没有那些注释，用注释解析会一条都匹配不到（踩过）。

用法：在仓库根目录执行  python3 scripts/fetch-fonts.py
"""
import os
import re
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(REPO, "fonts")
INDEX = os.path.join(REPO, "index.html")
CSS_BASE = "https://miaoda.feishu.cn/fonts/css2?{}&display=swap"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36")

FAMILIES = [("Manrope", "wght@400;500;600;700"),
            ("IBM Plex Mono", "wght@400;500;600"),
            ("Noto Sans SC", "wght@400;500;600;700")]

FACE_RE = re.compile(r"@font-face\s*\{(.*?)\}", re.S)
FIELD = {
    "family": re.compile(r"font-family:\s*'([^']+)'"),
    "weight": re.compile(r"font-weight:\s*(\d+)"),
    "url": re.compile(r"url\((https://[^)]+\.woff2)\)"),
    "range": re.compile(r"unicode-range:\s*([^;]+);"),
}


def fetch_css(family, axis):
    url = CSS_BASE.format("family=" + family.replace(" ", "+") + ":" + axis)
    out = subprocess.run(["curl", "-s", "--max-time", "90", "-A", UA, url],
                         capture_output=True, text=True, check=True).stdout
    if "@font-face" not in out:
        sys.exit("拉取字体 CSS 失败：" + url)
    return out


def parse_range(spec):
    out = []
    for part in spec.split(","):
        m = re.fullmatch(r"[Uu]\+([0-9A-Fa-f]+)(?:-([0-9A-Fa-f]+))?", part.strip())
        if m:
            lo = int(m.group(1), 16)
            hi = int(m.group(2), 16) if m.group(2) else lo
            out.append((lo, hi))
    return out


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def main():
    if os.path.isdir(FONT_DIR):
        shutil.rmtree(FONT_DIR)
    os.makedirs(FONT_DIR)

    html = open(INDEX, encoding="utf-8").read()
    # 注意：拉丁字体要渲染**动态内容**（时间戳、日期、偏移），所以必须带上完整可打印 ASCII，
    # 不能只用源码里出现过的字符。中文则全部来自字符串字面量，源码集合已完整。
    used = {ord(c) for c in html} | set(range(0x20, 0x7F))
    print("需要的码点数：{}（其中 CJK {}）".format(
        len(used), len({c for c in used if c > 0x2E80})))

    jobs = []
    for family, axis in FAMILIES:
        css = fetch_css(family, axis)
        faces = FACE_RE.findall(css)
        kept = 0
        for body in faces:
            f = FIELD["family"].search(body)
            w = FIELD["weight"].search(body)
            u = FIELD["url"].search(body)
            r = FIELD["range"].search(body)
            if not (f and w and u) or f.group(1) != family:
                continue
            if r:
                ranges = parse_range(r.group(1))
                need = sorted(cp for cp in used if any(lo <= cp <= hi for lo, hi in ranges))
                if not need:
                    continue          # 该分片覆盖的字页面一个都不用 → 丢弃
                spec = r.group(1).strip()
            else:
                need = sorted(used)    # 无 unicode-range = 覆盖全部
                spec = None
            kept += 1
            jobs.append((family, w.group(1), u.group(1), spec, need))
        print("  {}: 分片命中 {} / 共 {}".format(family, kept, len(faces)))

    lines = ["/* 由 scripts/fetch-fonts.py 生成，请勿手工编辑。",
             "   自托管：Manrope + IBM Plex Mono + Noto Sans SC。",
             "   筛选依据「unicode-range ∩ index.html 实际用到的码点」，并逐个分片做子集化；",
             "   中文因此能在**字形不变**的前提下压到几百 KB。",
             "   字体来源 Google Fonts，SIL Open Font License 1.1。 */", ""]
    bytetotal, seq = 0, {}
    for family, weight, url, spec, need in jobs:
        key = slug(family) + "-" + weight
        seq[key] = seq.get(key, 0) + 1
        name = "{}-{:02d}.woff2".format(key, seq[key])
        raw = os.path.join(FONT_DIR, "._raw.woff2")
        subprocess.run(["curl", "-s", "--max-time", "120", "-A", UA, url, "-o", raw], check=True)
        dest = os.path.join(FONT_DIR, name)
        unicodes = ",".join("U+%04X" % cp for cp in need)
        r = subprocess.run(["pyftsubset", raw, "--unicodes=" + unicodes,
                            "--flavor=woff2", "--output-file=" + dest],
                           capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(dest):
            sys.exit("子集化失败（{} {}）：{}".format(family, weight, (r.stderr or "")[-300:]))
        os.remove(raw)
        bytetotal += os.path.getsize(dest)
        lines += ["@font-face {", "  font-display: swap;",
                  "  font-family: '{}';".format(family), "  font-style: normal;",
                  "  font-weight: {};".format(weight),
                  "  src: url(fonts/{}) format('woff2');".format(name)]
        if spec:
            lines.append("  unicode-range: {};".format(spec))
        lines += ["}", ""]

    open(os.path.join(REPO, "fonts.css"), "w", encoding="utf-8").write("\n".join(lines))

    # —— 自检：语法闭合 + 覆盖完整，任一不过就非零退出 ——
    css_out = open(os.path.join(REPO, "fonts.css"), encoding="utf-8").read()
    unclosed = len(re.findall(r"url\(fonts/[^)]*woff2\s+format", css_out))
    good = len(re.findall(r"url\(fonts/[^)]*woff2\)\s+format", css_out))
    ranges = [r for spec in FIELD["range"].findall(css_out) for r in parse_range(spec)]
    missing = sorted(c for c in used if c > 0x7F
                     and not any(lo <= c <= hi for lo, hi in ranges))
    print("\n字体 {} 个，合计 {:.0f} KB | @font-face {}".format(len(jobs), bytetotal / 1024, good))
    print("语法自检：未闭合 url( = {}（须为 0）".format(unclosed))
    print("覆盖自检：非 ASCII 码点未被覆盖 {} 个（须为 0）".format(len(missing)))
    if unclosed or missing:
        sys.exit("自检未通过：未闭合 {}，漏字 {}".format(unclosed, len(missing)))


if __name__ == "__main__":
    main()
