#!/usr/bin/env python3
"""Build the editable artifact from max-src.html (Sarah's make-editable.py, adapted to Max's anchors).

The editable page is the same map with copy editing on by default and a Save button that publishes
a new version of the artifact (claude.use('artifact').publish(html)) with the edited copy baked into
a <script id="copy-data"> block. The page carries its own canonical template (base64, <script id="tpl">)
so it can regenerate a complete document without serialising the live DOM.
Output: max-editable.html — publish that file with the Artifact tool, capabilities {artifact: {}}.
To bake Tanner's edits: Artifact read the editor URL → parse the copy-data JSON → diff vs the .ed defaults here → apply.
"""
import base64, json, os, re, time
here = os.path.dirname(os.path.abspath(__file__))
E = open(os.path.join(here, 'max-src.html')).read()

def must(old, new, count=1):
    global E
    assert E.count(old) == count, (E.count(old), old[:80])
    E = E.replace(old, new)

# title (a name, not a caption)
must("<title>Max's Practice Map</title>", "<title>Max's Practice Map Editor</title>")

# edit bar: Save · Copy for Claude · Preview
must('<span>Editing copy — tap any text to change it. Changes save as you type.</span>',
     '<span>Tap any text to change it. Edits stay on this device until you tap Save, which writes them into this page.</span>')
must('<button id="copyAll" type="button">Copy for Claude</button>\n  <button id="editDone" type="button">Done</button>',
     '<button id="saveCopy" class="primary" type="button">Save</button>\n  <button id="copyAll" type="button">Copy for Claude</button>\n  <button id="editDone" type="button">Preview</button>')

# CSS: primary button, visible "Edit copy" link in preview mode
must('.edlink { display: none; color: var(--accent);', '.edlink { display: inline; color: var(--accent);')
must("#editbar .edn button.on { background: var(--accent); border-color: var(--accent); color: var(--ink); }",
     "#editbar .edn button.on { background: var(--accent); border-color: var(--accent); color: var(--ink); }\n#editbar button.primary { background: var(--accent); border-color: var(--accent); color: var(--ink); }\n#editbar button.primary[disabled] { opacity: .55; cursor: default; }")

# header comment
must("<!--\n  Max's Practice Map — same build", "<!--\n  EDITABLE VERSION (Tanner's copy-editing surface; Max never sees this one). Save publishes a new\n  version of this artifact with the copy in <script id=\"copy-data\">; read that block back to bake edits into max-src.html.\n  Max's Practice Map — same build")

# template + copy data blocks, right before the app script
must('<script>\n/* ---------- preview vs. live ----------',
     '<script id="tpl" type="text/plain">__TPL_B64__</script>\n<script id="copy-data" type="application/json">__COPY_JSON__</script>\n<script>\n/* ---------- preview vs. live ----------')

# JS: replace the load/edit/save wiring between two anchors
start = E.index('/* load: copy.json (repo) → localStorage → defaults */')
end = E.index('/* ---------- practice sessions: "Softening Date" (per-viewer) ----------')
new_js = r'''/* load: the copy baked into this version (copy-data) → unsaved edits kept on this device for that version → defaults */
var copyEl = document.getElementById('copy-data'), tplEl = document.getElementById('tpl');
var PAGE = {}; try { PAGE = JSON.parse(copyEl.textContent || '{}') || {}; } catch (e) { PAGE = {}; }
var PAGE_V = PAGE._v || 0, dirty = false;
apply(PAGE);
(function loadLocal() {
  var local = null; try { local = JSON.parse(localStorage.getItem(CKEY) || 'null'); } catch (e) {}
  if (local && local.base === PAGE_V && local.copy) { apply(local.copy); dirty = true; note('unsaved edits — tap Save', true); }
  else if (local) { try { localStorage.removeItem(CKEY); } catch (e) {} } /* a newer version was published since; its copy wins */
})();
function stash() { try { localStorage.setItem(CKEY, JSON.stringify({ base: PAGE_V, copy: collect() })); } catch (e) {} }
/* mode: this is the editing surface, so editing is on unless Tanner switched to Preview */
var mode = 'edit'; try { mode = localStorage.getItem('max-map-mode') || 'edit'; } catch (e) {}
setEdit(mode !== 'preview' || location.hash === '#edit');
window.addEventListener('hashchange', function () { if (location.hash === '#edit') setEdit(true); });
document.getElementById('editDone').onclick = function () { setEdit(false); try { localStorage.setItem('max-map-mode', 'preview'); } catch (e) {} };
document.getElementById('editToggle').onclick = function () { setEdit(true); try { localStorage.setItem('max-map-mode', 'edit'); } catch (e) {} };
EDS.forEach(function (el) {
  el.addEventListener('input', function () { dirty = true; stash(); note('unsaved edits — tap Save', true); });
});
document.getElementById('copyAll').onclick = function () {
  var lines = EDS.map(function (el) { return (el.getAttribute('data-key') || '?') + ' — ' + el.textContent.replace(/\s+/g, ' ').trim(); });
  var text = 'Max\'s Practice Map — copy\n\n' + lines.join('\n');
  function done() { note('copied'); }
  if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, done); else done();
};

/* ---------- save: publish a new version of this artifact with the copy baked in ----------
   The page's canonical template lives in #tpl (base64, a complete document with two slots); Save fills
   the slots — the template itself, and the copy JSON — and hands the shell the result. Never the live DOM.
   After a successful publish the shell reloads this view to the new version. */
var saveBtn = document.getElementById('saveCopy'), artifactNS = null, artifactKnown = false;
function b64d(s) { return decodeURIComponent(Array.prototype.map.call(atob(s), function (c) { return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2); }).join('')); }
function buildDoc(copy) {
  var b64 = tplEl.textContent.trim(), T = b64d(b64);
  var jsonText = JSON.stringify(copy).replace(/</g, '\\u003c');
  return T.replace('__TPL' + '_B64__', function () { return b64; }).replace('__COPY' + '_JSON__', function () { return jsonText; });
}
function readOnly(msg) { artifactNS = null; saveBtn.disabled = true; note(msg || 'Saving is unavailable here — use Copy for Claude', true); }
if (window.claude && typeof window.claude.use === 'function') {
  window.claude.use('artifact').then(function (ns) { artifactKnown = true; if (ns) artifactNS = ns; else readOnly(); }, function () { artifactKnown = true; readOnly(); });
} else { readOnly(); }
saveBtn.onclick = function () {
  if (!artifactNS) { readOnly(artifactKnown ? undefined : 'Still connecting — try again in a moment'); return; }
  var copy = collect(); copy._v = Date.now();
  var html; try { html = buildDoc(copy); } catch (e) { note('Couldn\'t build the page — use Copy for Claude', true); return; }
  saveBtn.disabled = true; note('Saving…', true);
  try { localStorage.removeItem(CKEY); } catch (e) {}
  artifactNS.publish(html).then(function () { note('Saved — reloading', true); }, function (err) {
    var code = (err && err.code) || 'upstream_error';
    if (code === 'conflict') { note('A newer version was just published — reloading to it', true); return; }
    stash(); saveBtn.disabled = false;
    if (code === 'not_writer' || code === 'not_granted' || code === 'not_declared' || code === 'capability_disabled' || code === 'capability_removed' || code === 'consent_required') readOnly('This view can\'t save — use Copy for Claude');
    else if (code === 'too_large') note('Too large to save — use Copy for Claude', true);
    else if (code === 'rate_limited') note('Saving too often — wait a moment, then Save again', true);
    else note('Couldn\'t save (' + code + ') — try once more, or Copy for Claude', true);
  });
};

'''
E = E[:start] + new_js + E[end:]

# the complete document the page republishes (slots left open)
T = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
     '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
     '<meta name="color-scheme" content="light">\n<style>img{max-width:100%}</style>\n</head>\n<body>\n'
     + E + '\n</body>\n</html>\n')
assert T.count('__TPL_B64__') == 1 and T.count('__COPY_JSON__') == 1, (T.count('__TPL_B64__'), T.count('__COPY_JSON__'))
b64 = base64.b64encode(T.encode('utf-8')).decode('ascii')
initial = json.dumps({'_v': int(time.time() * 1000)})
out = E.replace('__TPL_B64__', b64).replace('__COPY_JSON__', initial)
open(os.path.join(here, 'max-editable.html'), 'w').write(out)

# sanity: simulate the page rebuilding itself from #tpl
m = re.search(r'<script id="tpl" type="text/plain">([A-Za-z0-9+/=]+)</script>', out)
T2 = base64.b64decode(m.group(1)).decode('utf-8')
assert T2 == T
doc2 = T2.replace('__TPL_B64__', m.group(1)).replace('__COPY_JSON__', json.dumps({'_v': 1, 'title': 'x'}))
assert doc2.startswith('<!doctype html>') and doc2.count(m.group(1)) == 1 and '"title": "x"' in doc2 and '__TPL_B64__' not in doc2
print('max-editable.html', len(out), 'bytes; template', len(T), 'bytes; round-trip ok')
