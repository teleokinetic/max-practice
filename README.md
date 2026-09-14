# Max's Practice Map

Max's installable practice dashboard (PWA): a Library of four recordings with in-page players that resume where he left off, quiet completion states, and notes that mail back to Tanner. Same build as the other Practice Maps (Jan, Joe, Sarah). Served via GitHub Pages.

Build: edit `max-src.html` → `python3 wrap.py` → `index.html`. Bump `CACHE` in `sw.js` on every deploy. `python3 make-editable.py` builds the copy-editing artifact (`max-editable.html`, not committed).
