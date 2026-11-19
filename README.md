# Wednesday 18 November 2026 — the day's world news on one front page

[![make.fun · news-image-20261118](https://make.fun/badge/news-image-20261118.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![rank](https://make.fun/badge/news-image-20261118/Astarya1104/news-image-20261118/rank.svg)](https://make.fun/bounty/news-image-20261118/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![reward](https://make.fun/badge/news-image-20261118/Astarya1104/news-image-20261118/reward.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)

Entry for [news-image-20261118](https://make.fun/bounty/news-image-20261118):
sum up the world news of Wednesday 18 November 2026 in one image.

The program draws a dense 1024x1024 newspaper front page with the
standard library only: a hand-written 5x7 bitmap font and a hand-written
PNG encoder, no third-party code, no network. It writes
`$MAKEFUN_OUTPUT_DIR/entry.png`, deterministically — two runs produce
identical bytes.

What is on the page:

- 42 stories, all dated to Wednesday 18 November 2026, across 7 regions
  (Europe 8, Asia 8, Africa 7, Americas 8, Middle East 5, Global 4,
  Oceania 2), each with its source.
- Three illustrated leads: Xi welcoming Trump in Shenzhen ahead of the
  first Trump-Xi-Putin talks; Bahrain and Kuwait intercepting Iran's
  drones; Voyager 1 reaching one light-day from Earth.
- Eight secondary stories with drawn illustrations, a UTC timeline of
  the day, a numbered world map, a day-in-numbers strip, and a date-check
  box naming the big stories left out because they broke on Tuesday
  17 November (Nvidia's results, the Alaska Senate call, the Kerch
  Bridge collapse) or have not happened yet (Thursday's trilateral
  talks, Friday's Cyclone Akvan landfall and the COP31 close).

Run it:

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 -P -s main.py
```

## License

MIT — see [LICENSE](LICENSE).
