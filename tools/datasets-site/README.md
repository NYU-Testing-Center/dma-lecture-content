# Dataset browser

Builds the static site in `datasets/` (published by GitHub Pages at
https://nyu-testing-center.github.io/dma-lecture-content/datasets/).

It collects every CSV, SQLite and JSON data file from this repo's notebooks and
from the PrairieLearn course repo (`~/pl-nyu-cs479`), removes duplicates, and
lists where each is used in lectures and assignments only. Quizzes, exams and
practice/sample finals are never mentioned.

To rebuild after the data changes:

```
python3 inventory.py   # scan both repos; writes inventory.json (not committed)
python3 build.py       # writes ../../datasets/
```

`index.html` here is the page source; `build.py` inlines the dataset catalog
into it. Data files are stored gzip-compressed and base64-encoded as `.txt`.
`sql-wasm.wasm` is sql.js 1.10.3 from cdnjs.
