# eyecatch-generator

A template generator for note article header images (eyecatch), 1280×670 PNG.
Built for **Digital Basement** (note: sumaho_lab) to mass-produce headers in one unified design.

## Design

- The mascot character is the hero: large on the right, sticker-style white outline
- One background for every genre (cream → gold gradient); genre color appears **only as an accent** (badge, title bar, bottom stripe), so every article reads as "one of ours" at a glance
- Fixed brand pill in the bottom-left
- Titles wrap automatically (up to 4 lines, auto font size); put `｜` in the title to force a line break

## Usage

```bash
pip install weasyprint pymupdf pillow
python make_eyecatch.py "記事タイトル" --theme pc -o out.png
```

| Argument | Required | Description |
|---|---|---|
| `title` | ✓ | Article title |
| `-o` / `--out` | | Output PNG path (default: `eyecatch.png`) |
| `--theme` | | `neiro` (default) / `pc` / `smartphone` / `shikaku` / `security` / `life` |
| `--category` | | Badge text override; `""` hides the badge |
| `--face` | | Character expression: `smile` (default) / `wink` / `angry` / `sleepy` / `base` |

## Character assets

`assets/neiro_smile.png` (the default face, pre-cut transparent PNG) is included, so the generator works out of the box.
For the other expressions, put the white-background source WebP files listed in `FACES` into `assets/faces/` — the script cuts them out and caches the result in `assets/` on first use.

To use your own character, replace the PNG in `assets/` and adjust `FACES` / the brand label in the script.

---

By Digital Basement — a human troubleshooter and an AI partner, Kohaku.
