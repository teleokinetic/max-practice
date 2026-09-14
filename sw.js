/* Max's Practice Map — offline support.
   The shell (page, manifest, icons) is precached and refreshed in the background on every load; the lesson
   MP3s are cached best-effort at install and served with Range support so seeking works offline.
   copy.json (if ever added) is never served from cache. Bump CACHE on every deploy. */
var CACHE = "max-map-v1";
var SHELL = ["./", "./index.html", "./manifest.webmanifest",
             "./icon-192.png", "./icon-512.png", "./icon-maskable-512.png", "./apple-touch-icon.png"];
var AUDIO = ["./audio/pelvis-head.mp3", "./audio/feet-breath-belly.mp3", "./audio/session-practice.mp3", "./audio/pelvic-floor.mp3"];

self.addEventListener("install", function (e) {
  e.waitUntil((async function () {
    var c = await caches.open(CACHE);
    await c.addAll(SHELL);
    // Large files: cache one by one, never fail the install over them.
    for (var i = 0; i < AUDIO.length; i++) {
      try { if (!(await c.match(AUDIO[i]))) await c.add(AUDIO[i]); } catch (err) {}
    }
    self.skipWaiting();
  })());
});

self.addEventListener("activate", function (e) {
  e.waitUntil((async function () {
    var names = await caches.keys();
    await Promise.all(names.filter(function (n) { return n !== CACHE; })
      .map(function (n) { return caches.delete(n); }));
    await self.clients.claim();
  })());
});

async function serveAudio(req) {
  var cache = await caches.open(CACHE);
  var hit = await cache.match(req.url, { ignoreSearch: true });
  if (!hit) {
    // Not cached yet: stream from network, and cache the full file in the background.
    fetch(req.url).then(function (r) { if (r.ok) cache.put(req.url, r); }).catch(function () {});
    return fetch(req);
  }
  var blob = await hit.blob();
  var range = req.headers.get("range");
  if (!range) {
    return new Response(blob, { headers: {
      "Content-Type": "audio/mpeg", "Content-Length": String(blob.size), "Accept-Ranges": "bytes" } });
  }
  var m = /bytes=(\d+)-(\d*)/.exec(range);
  var start = m ? parseInt(m[1], 10) : 0;
  var end = (m && m[2]) ? parseInt(m[2], 10) : blob.size - 1;
  end = Math.min(end, blob.size - 1);
  return new Response(blob.slice(start, end + 1), {
    status: 206,
    headers: {
      "Content-Type": "audio/mpeg",
      "Content-Range": "bytes " + start + "-" + end + "/" + blob.size,
      "Content-Length": String(end - start + 1),
      "Accept-Ranges": "bytes"
    }
  });
}

self.addEventListener("fetch", function (e) {
  var url = new URL(e.request.url);
  if (e.request.method !== "GET") return; // note-sending (FormSubmit POST) etc. → network

  // copy.json is fetched with cache: 'no-store' — always let it go to network.
  if (url.origin === location.origin && /copy\.json$/.test(url.pathname)) return;

  if (url.origin === location.origin && url.pathname.indexOf("/audio/") !== -1) {
    e.respondWith(serveAudio(e.request));
    return;
  }

  if (url.origin === location.origin) {
    // shell: cache-first, refresh in background
    e.respondWith((async function () {
      var cached = await caches.match(e.request, { ignoreSearch: true });
      var net = fetch(e.request).then(function (r) {
        if (r.ok) caches.open(CACHE).then(function (c) { c.put(e.request, r.clone()); });
        return r;
      }).catch(function () { return cached; });
      return cached || net;
    })());
    return;
  }

  if (url.hostname === "fonts.googleapis.com" || url.hostname === "fonts.gstatic.com") {
    // fonts: cache-first so typography survives offline
    e.respondWith((async function () {
      var cached = await caches.match(e.request);
      if (cached) return cached;
      try {
        var r = await fetch(e.request);
        if (r.ok || r.type === "opaque") { var c = await caches.open(CACHE); c.put(e.request, r.clone()); }
        return r;
      } catch (err) { return Response.error(); }
    })());
  }
  // any other cross-origin request: not intercepted → network
});
