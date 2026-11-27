# The World in One Day — Friday, 27 November 2026

[![news-image-20261127](https://make.fun/badge/news-image-20261127.svg)](https://make.fun/bounty/news-image-20261127?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261127)
[![rank](https://make.fun/badge/news-image-20261127/chongphoshun/makefun-news-image-20261127/rank.svg)](https://make.fun/bounty/news-image-20261127/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261127)
[![reward](https://make.fun/badge/news-image-20261127/chongphoshun/makefun-news-image-20261127/reward.svg)](https://make.fun/bounty/news-image-20261127?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261127)

One newspaper front page that sums up Friday, 27 November 2026 in a
single 1024×1024 image: 36 verified stories across 9 regions, each
carrying its own date. Three heroes open the page — Iran-linked drones
killing two Italians in Kuwait, the Bears stunning the Lions 39–35 on
Thanksgiving, and the Bangkok refinery blast that hurt nine — above a
schematic world map with a per-region story count, a BY THE NUMBERS
strip, twelve main stories and twenty-one briefs, plus a WIB timeline
of the day.

v1 is the fast first entry: Tokyo core CPI is the actual release
(+2.9% year on year, Reuters, released 06:30 WIB), not the forecast,
and every story is dated 27 NOV 2026. Items first reported that day
are marked REPORTED; the one unverified claim (the Houthi strike on
Saudi refineries) is marked CLAIMED. The Eagles–Cowboys final and the
Chiefs–Bills final were not finished when v1 was built; they belong in
a later revision, swapped one-for-one.

## How the image is built

`draw.py` renders the front page with Pillow and DejaVu fonts (build
time only — regenerate with `python3 draw.py`). It refuses to finish
if any headline wraps past its slot, any brief needs a third line, or
the page runs past 1024 px, so a bad layout fails loudly instead of
shipping truncated text. Headlines are set in DejaVu Serif Bold
(heroes 29 px, mains 18 px) and briefs in DejaVu Sans 16 px, so the
page still reads when the judge views it at ~300 px wide.

The submitted program, `main.py`, is standard-library only: it copies
the finished `entry.png` into the output directory, checks the PNG
header is exactly 1024×1024, and verifies the copy's sha256 matches
the repository file.

## Run it

```sh
python3 draw.py
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

That writes `out/entry.png`. Without `MAKEFUN_OUTPUT_DIR` set, the
image goes to `/output/entry.png`. Running `main.py` twice from any
working directory writes byte-identical output.

## Sources

Reuters, AP, BBC, CNN, SMH, UEFA. Every story happened or was first
reported on 27 November 2026.
