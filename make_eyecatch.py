#!/usr/bin/env python3
"""デジタル地下室 note見出し画像（アイキャッチ）ジェネレータ

使い方:
    python make_eyecatch.py "タイトル" -o out.png [--theme pc] [--category "PCトラブル"] [--face smile]

サイズは note 推奨の 1280×670 px。
デザインは「ちびねいろ」のキャラ色（金髪ゴールド＋黒＋紫）を主役にし、
ジャンル色はバッジとラインの差し色だけに使う。

実行には pdf-venv の Python を使うこと:
    ~/workspace/tools/pdf-venv/bin/python make_eyecatch.py ...
"""

import argparse
import html
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
MEDIA_DIR = os.path.join(ASSETS_DIR, "faces")

W, H = 1280, 670

# ちびねいろの表情バリエーション（素材ファイル名）
FACES = {
    "smile": "media-generation-neiro-chibi-bob-smile2-0-587d11b9-8498-4162-b358-3dd2c15e39c9.webp",
    "wink": "media-generation-neiro-chibi-bob-nofreckles-0-7b60c475-46a9-44f9-aca4-d4d68835bf70.webp",
    "angry": "media-generation-neiro-chibi-bob-angry3-0-fd1bc0a1-9f77-4a6b-8444-cf0d23a5df60.webp",
    "sleepy": "media-generation-neiro-chibi-bob-sleepy2-0-7f6f26ae-e500-440c-b6b1-0797c2c573f1.webp",
    "base": "media-generation-neiro-chibi-bob-0-aefd266b-b703-437f-8013-01bde2c03597.webp",
}

# ジャンル別テーマ（accent=差し色, label=バッジのデフォルト文言）
THEMES = {
    "neiro":      {"accent": "#E8A812", "label": "デジタル地下室"},
    "pc":         {"accent": "#2E9E5B", "label": "PCトラブル"},
    "smartphone": {"accent": "#2E7CD6", "label": "スマホ"},
    "shikaku":    {"accent": "#F08A1D", "label": "IT資格"},
    "security":   {"accent": "#7C4DBD", "label": "セキュリティ"},
    "life":       {"accent": "#E05A8D", "label": "生活・家電"},
}


# ---------------------------------------------------------------- キャラ切り抜き
def get_character_png(face: str) -> str:
    """白背景のステッカー風WebPからキャラを透過PNGに切り抜き、キャッシュする。"""
    out = os.path.join(ASSETS_DIR, f"neiro_{face}.png")
    if os.path.exists(out):
        return out
    src = os.path.join(MEDIA_DIR, FACES[face])
    if not os.path.exists(src):
        sys.exit(f"キャラ素材が見つかりません: {src}")

    from PIL import Image, ImageDraw

    im = Image.open(src).convert("RGB")
    w, h = im.size
    marker = (255, 0, 255)
    # 画像の縁の複数点からフラッドフィルして白背景（＋淡い影）をマーカー色に塗る
    seeds = [
        (0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
        (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2),
        (w // 4, 0), (3 * w // 4, 0), (w // 4, h - 1), (3 * w // 4, h - 1),
    ]
    for xy in seeds:
        if im.getpixel(xy) != marker:
            ImageDraw.floodfill(im, xy, marker, thresh=52)

    rgba = im.convert("RGBA")
    px = rgba.load()
    # マーカー色を透過に変換（走査はnumpyで高速化）
    import numpy as np

    arr = np.array(rgba)
    mask = (arr[:, :, 0] == 255) & (arr[:, :, 1] == 0) & (arr[:, :, 2] == 255)
    arr[:, :, 3] = np.where(mask, 0, 255)
    rgba = Image.fromarray(arr, "RGBA")
    bbox = rgba.getbbox()
    if bbox:
        pad = 8
        bbox = (
            max(0, bbox[0] - pad),
            max(0, bbox[1] - pad),
            min(rgba.width, bbox[2] + pad),
            min(rgba.height, bbox[3] + pad),
        )
        rgba = rgba.crop(bbox)
    os.makedirs(ASSETS_DIR, exist_ok=True)
    rgba.save(out)
    return out


# ---------------------------------------------------------------- タイトル整形
def text_units(s: str) -> float:
    """全角=1.0、半角=0.52 として文字列の見かけ幅を概算する。"""
    u = 0.0
    for ch in s:
        u += 0.52 if ord(ch) < 0x2E80 else 1.0
    return u


BREAK_AFTER = "｜、。（）」』はがをにのへとやも"
# 行頭に来ると不自然な文字（促音・拗音・長音・句読点・閉じ括弧）
NO_LINE_START = "ーッャュョァィゥェォ、。・」』）】"


def wrap_title(title: str, max_units: float = 11.5) -> list[str]:
    """タイトルを行リストに整形する。明示改行と「｜」を優先し、長い行は助詞等で折る。"""
    raw_lines: list[str] = []
    for part in title.replace("｜", "\n").split("\n"):
        part = part.strip()
        if part:
            raw_lines.append(part)

    lines: list[str] = []
    for line in raw_lines:
        while text_units(line) > max_units and len(line) > 6:
            # max_units を超えない範囲で、最後に出てくる区切り位置で折る
            best = -1
            best_units = 0.0
            acc = 0.0
            limit = len(line)
            for i, ch in enumerate(line):
                acc += 0.52 if ord(ch) < 0x2E80 else 1.0
                if acc > max_units:
                    limit = i
                    break
                if ch in BREAK_AFTER:
                    best = i + 1
                    best_units = acc
            if best <= 0 or best_units < max_units * 0.5:
                # 区切りが無い／早すぎる場合は上限位置で折る（行頭禁則は避ける）
                best = max(1, limit)
                while best > 1 and line[best] in NO_LINE_START:
                    best -= 1
            lines.append(line[:best])
            line = line[best:]
        if line:
            lines.append(line)
    return lines[:4]


def pick_font_size(lines: list[str]) -> int:
    # キャラに重ならないよう、タイトル幅は約700px以内に収める
    max_u = max(text_units(l) for l in lines)
    size = int(700 / max_u) if max_u else 100
    cap = 104 if len(lines) == 1 else 96 if len(lines) == 2 else 84
    return max(54, min(size, cap))


# ---------------------------------------------------------------- HTML生成
def build_html(title: str, theme: str, category: str | None, chara_uri: str) -> str:
    t = THEMES[theme]
    accent = t["accent"]
    cat = category if category is not None else t["label"]
    lines = wrap_title(title)
    size = pick_font_size(lines)
    title_html = "<br>".join(html.escape(l) for l in lines)
    badge_html = (
        f'<div class="badge">{html.escape(cat)}</div>' if cat else ""
    )
    # 4行タイトルではブランドピルと干渉するためバーを省略する
    bar_html = '<div class="bar"></div>' if len(lines) < 4 else ""
    return f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8"><style>
@page {{ size: {W}px {H}px; margin: 0; }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  width: {W}px; height: {H}px; overflow: hidden; position: relative;
  font-family: "Noto Sans CJK JP", sans-serif;
  background: linear-gradient(135deg, #FFF8E1 0%, #FFEFC0 45%, #FFDF8E 100%);
}}
/* 装飾の丸（控えめ） */
.deco1 {{ position: absolute; width: 520px; height: 520px; border-radius: 50%;
  background: rgba(255,255,255,0.35); top: -260px; right: 180px; }}
.deco2 {{ position: absolute; width: 300px; height: 300px; border-radius: 50%;
  background: rgba(255,255,255,0.30); bottom: -170px; left: 300px; }}
/* キャラ後ろのグロー */
.glow {{ position: absolute; width: 560px; height: 560px; border-radius: 50%;
  background: radial-gradient(circle, rgba(255,255,255,0.85) 0%, rgba(255,255,255,0) 70%);
  right: -30px; top: 60px; }}
.chara {{ position: absolute; right: -6px; bottom: -24px; height: 706px; }}
.main {{ position: absolute; left: 64px; top: 0; width: 830px; height: 100%; }}
.badge {{
  display: inline-block; margin-top: 54px;
  background: {accent}; color: #fff; font-weight: 700;
  font-size: 30px; letter-spacing: 0.08em;
  padding: 10px 26px 12px; border-radius: 999px;
}}
.title {{
  margin-top: 32px; color: #2A2118; font-weight: 700;
  font-size: {size}px; line-height: 1.28; letter-spacing: 0.01em;
}}
.bar {{ margin-top: 26px; width: 128px; height: 12px; border-radius: 6px; background: {accent}; }}
.brand {{
  position: absolute; left: 64px; bottom: 52px;
  display: inline-block; background: #211B12; color: #fff;
  font-weight: 700; font-size: 27px; letter-spacing: 0.14em;
  padding: 12px 24px 14px 20px; border-radius: 10px;
}}
.brand .dot {{ color: #FFC93C; }}
.stripe {{ position: absolute; left: 0; bottom: 0; width: 100%; height: 16px; background: {accent}; }}
</style></head><body>
<div class="deco1"></div><div class="deco2"></div>
<div class="glow"></div>
<img class="chara" src="{chara_uri}">
<div class="main">
  {badge_html}
  <div class="title">{title_html}</div>
  {bar_html}
</div>
<div class="brand"><span class="dot">■</span> デジタル地下室</div>
<div class="stripe"></div>
</body></html>"""


# ---------------------------------------------------------------- レンダリング
def render(html_str: str, out_path: str) -> None:
    from weasyprint import HTML
    import pymupdf

    pdf_bytes = HTML(string=html_str, base_url=BASE_DIR).write_pdf()
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]
    zoom = W / page.rect.width
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
    # サイズが1pxずれた場合はリサイズして厳密に合わせる
    if pix.width != W or pix.height != H:
        from PIL import Image
        import io

        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        im = im.resize((W, H), Image.LANCZOS)
        im.save(out_path)
    else:
        pix.save(out_path)


def main() -> None:
    ap = argparse.ArgumentParser(description="note見出し画像ジェネレータ（1280×670）")
    ap.add_argument("title", help="記事タイトル（「｜」や改行で任意の改行も可）")
    ap.add_argument("-o", "--out", default="eyecatch.png", help="出力PNGパス")
    ap.add_argument("--theme", choices=list(THEMES), default="neiro",
                    help="ジャンルテーマ（差し色とバッジの既定文言が変わる）")
    ap.add_argument("--category", default=None,
                    help="バッジ文言を上書き（空文字で非表示）")
    ap.add_argument("--face", choices=list(FACES), default="smile",
                    help="ちびねいろの表情")
    ap.add_argument("--no-chara", action="store_true", help="キャラを入れない")
    args = ap.parse_args()

    chara_uri = ""
    if not args.no_chara:
        chara_path = get_character_png(args.face)
        chara_uri = "file://" + chara_path

    doc = build_html(args.title, args.theme, args.category, chara_uri)
    if args.no_chara:
        doc = doc.replace('<img class="chara"', '<img class="chara" style="display:none"')
    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    render(doc, out)
    print(f"OK: {out} ({W}x{H})")


if __name__ == "__main__":
    main()
