# CS 0479 — Data Management and Analysis

Lecture notebooks for the course. Each lecture is a Jupyter notebook you can
**read, run, and watch as a slideshow**.

```
notebooks/lecture-01-overview-of-tooling-for-data-management-and-analysis.ipynb
notebooks/lecture-02-python-fundamentals.ipynb
…
notebooks/lecture-33-graph-databases-neo4j.ipynb
```

---

## 1. Getting started

### Step 1 — fork this repository

Click **Fork** in the top-right of this page to create your own copy under your
GitHub account. Work in **your fork**, not in the course repository.

Forking means your notes, edits, and experiments are yours: nothing you do can
affect your classmates or the original material, and you can always compare
against the course copy.

### Step 2 — open a codespace on your fork

From your fork, click **Code → Codespaces → Create codespace on main**.

The codespace installs everything for you — Python, JupyterLab, and the
libraries the lectures use. When the codespace itself loads, plz don't 
click anything; allow the terminal to automatically initiate its main 
devcontainer process, which can take close to ten minutes.
**You never need to install anything or run a `pip` command.**

When it finishes, the terminal prints a box like this (make sure to scroll
to get the full terminal output):

```
  ┌──────────────────────────────────────────────────────────────┐
  │  DMA lecture decks — JupyterLab + RISE                       │
  └──────────────────────────────────────────────────────────────┘

  Open:  https://<your-codespace>-8888.app.github.dev/lab?token=…
```

**Click that link.** JupyterLab opens in a new browser tab. Open any lecture
from the `notebooks/` folder in the file browser on the left. BTW, you should
only have to deal with this ~10-min wait time once, when you create the codespace.
After that, the history should persist.

> **Lost the link?** Run this in the terminal:
>
> ```bash
> bash .devcontainer/start-jupyter.sh
> ```
>
> Add a lecture number to have the link open that lecture directly, instead of
> leaving you in the file browser:
>
> ```bash
> bash .devcontainer/start-jupyter.sh 29
> ```
>
> You can also find the server under the **Ports** tab (port 8888) — but use the
> printed link if you can, because it carries the `?token=…` the server needs.

> **The link must start with `https://` and end with `?token=…`.** If you are
> looking at a `http://127.0.0.1:8888` or `http://codespaces-…:8888` address,
> that is the address *inside* the container and your browser cannot reach it.
> Re-run the command above to get the real one.

---

## 2. Turning a lecture into a slideshow

### Step 1 — press `Esc`

This puts the notebook in *command mode*. If your cursor is blinking inside a
code cell, keyboard shortcuts get typed into the cell instead of running.

### Step 2 — press `Option` + `R`  &nbsp;(Windows/Linux: `Alt` + `R`)

The slideshow opens in a panel beside the notebook. Use the **⛶ fullscreen
button** in that panel's toolbar to fill the screen.

To close it, click the **×** on the slideshow panel's tab.

---

## 3. Moving around a slideshow

A deck is laid out in **two directions**, and the arrow keys do different jobs.

| Key | What it does |
| --- | --- |
| `→` / `←` | Move **forward / back one slide** — the main way through a lecture |
| `↓` / `↑` | Move **down into / back up out of** a live example's individual steps |
| `Space` / `Shift`+`Space` | Walks the whole deck in order, including every step of every live example |

### Why there are two directions

Most of a lecture is a straight left-to-right sequence, so `→` is all you need:

```
→   →   →   →   →   →
[1] [2] [3] [4] [5] [6]  …
```

A few live examples are long enough that their steps are stacked **underneath**
one slide instead of stretching the deck sideways. `→` treats the whole example
as a single stop and moves past it; `↓` walks through its steps:

```
→        →                  →
[4]     [5] LIVE EXAMPLE   [6]
         │
         ↓  step 1
         ↓  step 2
         ↓  step 3
```

So if you land on a 📈 `LIVE EXAMPLE` slide, press `↓` to work through it, then
`→` to carry on with the lecture. Only a couple of lectures use this — mainly
**Lecture 32 (MongoDB)**, whose example runs to about 40 steps.

**If you'd rather not think about it, use `Space`.** It goes through everything
in order and never skips a step, so you can hold to one key for a whole lecture.

If a slide has more content than fits on screen, just **scroll** — the slide
scrolls on its own.

### Running code during a lecture

Many slides hold real, runnable Python. Every code cell has a **▶ button** at
its top-left — click it to run that cell.

If you prefer the keyboard, click into the cell and use:

| Key | What it does |
| --- | --- |
| `Shift`+`Enter` | Run the cell and **stay on the current slide** |
| `Ctrl`+`Enter` or `Cmd`+`Enter` | Same thing |

The button pulses while the cell is running and returns to normal when it
finishes. Nothing here advances the slide — you move with `Space` or `→`.

Edit the code and re-run it as much as you like; it's your own copy and
you can't affect anyone else.

---

## 4. What you'll see in a lecture

**Content slides** — the material itself: explanations, diagrams, formulas, and
code you can run.

**Live examples** — a teal banner marked 📈 `LIVE EXAMPLE`, followed by a working
notebook. These are meant to be run. Press `↓` to step down through them, then
`→` to move on (see section 3).

**In-class exercises** — an amber card marked 🧪 `IN-CLASS EXERCISE`:

```
🧪 IN-CLASS EXERCISE
Finding Primes

Exercise link:  <PrairieLearn URL here>
```

These are **signposts, not the exercise**. The exercise itself lives in PrairieLearn,
don't try to do it inside the notebook.

---

## 5. What you can and can't safely change

**Safe to edit:** the notebooks in `notebooks/`. Change the code, add cells, take
notes, re-run whatever you like. That is what your fork is for.

**Please leave everything else alone.** In particular:

| Don't touch | Why |
| --- | --- |
| `.devcontainer/` | builds your codespace — a bad edit here means it won't start |
| `requirements.txt` | installs Python and the course libraries |
| `tools/` | generates the notebooks and configures the slideshow keys |

Editing those risks breaking your environment, and the failure usually shows up
later as a codespace that won't open or a slideshow that comes up blank. If you
only change files inside `notebooks/`, you can't get into that state.

Nothing is locked, so if you do break something, see the last two entries in
section 6 below.

---

## 6. If something goes wrong

**The slideshow is blank / white.**
Give it a few seconds — a deck takes a moment to build. Also click inside the
browser tab: browsers don't draw tabs you haven't focused yet.

**`Option+R` does nothing.**
Either you're in edit mode (press `Esc` first — see step 1), or you're in the
**VS Code notebook editor** rather than JupyterLab. The slideshow is a
JupyterLab feature; VS Code cannot run it. Editing in VS Code is fine, but
presenting needs the JupyterLab link from the terminal.

**A plot didn't appear.**
Run that example's cells in order from the top — later cells usually depend on
variables defined in earlier ones.

**I broke a notebook.**
`git checkout -- notebooks/` in a terminal restores every lecture to its
original state.

**I edited something outside `notebooks/` and things stopped working.**
`git checkout -- .` restores everything. If the codespace itself is broken, the
quickest fix is to delete it and create a new one — you lose nothing that you
have committed and pushed.

---

## 7. Running on your own machine instead

You don't have to use Codespaces:

```bash
bash present.sh          # opens the file browser
bash present.sh 29       # opens lecture 29 directly
```

This installs everything into a private `.venv/` (not your system or Anaconda
Python) and points Jupyter at an isolated `.jupyter-rise/` config directory
instead of your real `~/.jupyter`, so it can't affect any other Jupyter
project on your machine and vice versa. It's idempotent — if a server is
already running on port 8888 it just prints that server's link instead of
starting a second one — so re-run it any time you want the URL again.

The script prints a link like:

```
Open:  http://127.0.0.1:8888/lab?token=…
```

Click it, open a lecture from `notebooks/`, then press `Esc` and
`Option`+`R` (`Alt`+`R` on Windows/Linux) to enter the slideshow — same as
section 2 above.

If you have a local MongoDB server (`mongod`) installed, the script starts it
automatically for Lecture 32; otherwise everything except that lecture's
Mongo cells works fine.

### Why not just `pip install -r requirements.txt && jupyter lab`?

You can, but your JupyterLab **must not** have the `jupyter-widgets`,
`pyviz`/`panel`, `plotly`, or `variableinspector` extensions installed. RISE
can't load alongside them and the slideshow comes up blank. Anaconda
installations ship these by default, which is why both the codespace and
`present.sh` use a clean Python environment instead. If you're on Anaconda
and hit a blank slideshow running Jupyter directly, use `present.sh` (or the
codespace) instead.

## 8. Using Google Colab instead

Every lecture has an **Open in Colab** button just below its title. Click it to
open that lecture in [Google Colab](https://colab.research.google.com), with
nothing to install.

Lectures that read data files (CSV, JSON, XML, text and SQLite `.db` files)
have a **Colab setup** cell right after the button. **Run it first.** It
downloads this repository into Colab (a few seconds) and moves into the
`notebooks` folder, so the lecture's code finds its files exactly as it does in
a codespace. Outside Colab the cell does nothing.

Keep in mind:

- **Colab forgets everything when the session ends.** Run the setup cell again
  each time you reopen a lecture. Any files the lecture creates are lost unless
  you download them.
- **Save your own copy** with **File → Save a copy in Drive** if you want to
  keep your edits; the copy opened from GitHub is not saved.
- **Some things need a codespace or your own machine:** the slideshow view and
  the MongoDB (Lecture 32) and Neo4j (Lecture 33) servers.

---
