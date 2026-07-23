// Network-first cache for the app shell: always serve the latest deployed
// index.html when online, fall back to whatever was last cached when not.
// Since all business data is inlined into index.html itself, a cached copy
// gives full offline List-view browsing (search, filter, notes, applied) —
// only the Map tab needs a live connection (Google Maps JS SDK).
const CACHE = "lolo-job-hunt-v1";
const SHELL = ["./", "./index.html"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const isAppShell = event.request.mode === "navigate" || event.request.url.endsWith("index.html");
  if (!isAppShell) return;
  event.respondWith(
    fetch(event.request)
      .then((res) => {
        const clone = res.clone();
        caches.open(CACHE).then((c) => c.put(event.request, clone));
        return res;
      })
      .catch(() => caches.match(event.request).then((res) => res || caches.match("./index.html")))
  );
});
