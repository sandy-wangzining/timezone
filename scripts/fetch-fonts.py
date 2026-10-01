#!/usr/bin/env python3
"""把外部字体 CDN 改为自托管：只取 latin 子集，下载 woff2 并生成本地 fonts.css。

为什么只取 latin：
  - cyrillic / greek / vietnamese 子集对本工具无意义，白占体积；
  - Noto Sans SC（中文）会被切成上百个 unicode-range 分片，全量托管有好几 MB，
    而中文走系统字体（macOS 苹方 / Windows 雅黑）本来就是最常见做法。
    详见 README「字体」一节。

用法：在仓库根目录执行  python3 scripts/fetch-fonts.py
"""
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(REPO, "fonts")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36")

FAMILIES = [
    ("Manrope", "wght@400;500;600;700"),
    ("IBM Plex Mono", "wght@400;500;600"),
]

# 保留的子集：latin 是必需的；latin-ext 覆盖西欧扩展字符，一并留着（每片仅几 KB）
KEEP_SUBSETS = {"latin", "latin-ext"}

BLOCK_RE = re.compile(r"/\*\s*([a-z0-9-]+)\s*\*/\s*(@font-face\s*\{.*?\})", re.S)
FAMILY_RE = re.compile(r"font-family:\s*'([^']+)'")
WEIGHT_RE = re.compile(r"font-weight:\s*(\d+)")
URL_RE = re.compile(r"url\((https://[^)]+\.woff2)\)")


def fetch_css(query):
    url = "https://miaoda.feishu.cn/fonts/css2?{}&display=swap".format(query)
    out = subprocess.run(["curl", "-s", "--max-time", "60", "-A", UA, url],
                         capture_output=True, text=True, check=True).stdout
    if "@font-face" not in out:
        sys.exit("拉取字体 CSS 失败：{}".format(url))
    return out


def main():
    os.makedirs(FONT_DIR, exist_ok=True)
    faces = []
    for family, axis in FAMILIES:
        query = "family={}".format(family.replace(" ", "+")) + (":{}".format(axis) if axis else "")
        css = fetch_css(query)
        for subset, block in BLOCK_RE.findall(css):
            if subset not in KEEP_SUBSETS:
                continue
            m_url = URL_RE.search(block)
            m_fam = FAMILY_RE.search(block)
            m_wt = WEIGHT_RE.search(block)
            if not (m_url and m_fam and m_wt):
                continue
            faces.append({
                "subset": subset,
                "family": m_fam.group(1),
                "weight": m_wt.group(1),
                "url": m_url.group(1),
                "block": block,
            })

    if not faces:
        sys.exit("没有解析到任何 latin 子集的 @font-face")

    slug = lambda s: re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    total = 0
    rows = []
    seen = {}
    for f in faces:
        name = "{}-{}-{}.woff2".format(slug(f["family"]), f["weight"], f["subset"])
        dest = os.path.join(FONT_DIR, name)
        if name not in seen:
            subprocess.run(["curl", "-s", "--max-time", "90", "-A", UA, f["url"], "-o", dest],
                           check=True)
            seen[name] = os.path.getsize(dest)
        size = seen[name]
        total += size
        rows.append((name, size, f))
    # 去重（同一文件被多次引用时 total 会重复计入，这里按唯一文件重算）
    total = sum(seen.values())

    # 生成本地 fonts.css：把远端 url 换成本地相对路径，其余声明（unicode-range 等）原样保留
    css_lines = [
        "/* 由 scripts/fetch-fonts.py 生成，勿手工编辑。",
        "   字体来源：Google Fonts（Manrope / IBM Plex Mono，SIL Open Font License 1.1）。",
        "   只保留 latin / latin-ext 子集；中文不引网络字体，走系统字体。 */",
        "",
    ]
    for name, size, f in rows:
        block = f["block"]
        block = URL_RE.sub("url(fonts/{})".format(name), block)
        block = re.sub(r"\n\s*\n", "\n", block)
        css_lines.append("/* {} · {} · {} */".format(f["family"], f["weight"], f["subset"]))
        css_lines.append(block)
        css_lines.append("")
    with open(os.path.join(REPO, "fonts.css"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(css_lines))

    print("字体文件：{} 个，合计 {:.0f} KB".format(len(seen), total / 1024))
    for name, size in sorted(seen.items()):
        print("  {:44s} {:7.1f} KB".format(name, size / 1024))
    print("\n已生成 fonts.css（{} 个 @font-face）".format(len(rows)))


if __name__ == "__main__":
    main()
