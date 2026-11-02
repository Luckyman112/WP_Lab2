# LP-1170 — a syntax highlighter that prints like a line printer

Laboratory Work N2, Web Application Development Tools — Lab Variant 5 (Syntax Highlighter).

Type code on the left and it is highlighted on the right as a printout on
green bar fanfold paper. Highlighting is done on the server with Pygments;
the page sends the code after you stop typing and only reprints the lines
that changed.

## Project passport

| Student | Project Name | Brief project description | Framework | GitHub Link |
|---|---|---|---|---|
| _your name_ | LP-1170 Syntax Highlighter | Web app where you type code (15 languages, with auto-detection) and it is highlighted live on the server with Pygments. The result is shown as a line-printer listing; it can be saved ("filed"), reopened by link and downloaded as a standalone HTML file. | Django 6 + Pygments, vanilla JS | https://github.com/Luckyman112/WP_Lab2 |

## Dynamic elements

**Page load**
- status lamps switch on one after another (Power → Ready → On line);
- the paper feeds out of the printer slot;
- the listing is struck line by line, left to right, in steps like a print head;
- the line counter ticks up to the number of lines.

**Highlighting**
- live highlighting while typing (debounced `fetch` to `/api/highlight/`);
- only changed lines are reprinted, with the print-head animation;
- the Ready lamp blinks while you type, the Printing lamp is on during a request;
- language auto-detection, shown under the editor ("auto → Python");
- ribbon switch (black/red, carbon, colour) and paper switch (green bar, blue bar, plain), remembered in the browser;
- Tab indents, Ctrl+Enter files the job;
- "Tear off & file" saves the listing, animates the sheet being torn off and opens its permanent page.

## Running locally

Requires Python 3.11+.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/.

Tests: `python manage.py test printer`

## Structure

```
lineprinter/            Django project settings and root URLs
printer/
  highlight.py          Pygments rendering, per-line split, language detection
  models.py             Printout (a filed listing)
  views.py              page, JSON API (highlight, file), download
  templates/printer/    index.html, export.html (standalone download)
  static/printer/       paper.css, console.css, printer.js
  tests.py
```

## Routes

| URL | Purpose |
|---|---|
| `/` | editor with a sample listing |
| `/p/<slug>/` | a filed printout |
| `/p/<slug>/download/` | the printout as a standalone HTML file |
| `POST /api/highlight/` | `{code, language}` → highlighted lines |
| `POST /api/file/` | `{code, language, title}` → saves, returns URL |
| `/admin/` | Django admin |
