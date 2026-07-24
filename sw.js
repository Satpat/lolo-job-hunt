// Network-first cache for the app shell: always serve the latest deployed
// index.html when online, fall back to whatever was last cached when not.
// Since all business data is inlined into index.html itself, a cached copy
// gives full offline List-view browsing (search, filter, notes, applied) —
// only the Map tab needs a live connection (Google Maps JS SDK). The resume
// builder also works offline (editing + PDF/Word export); only its "Tailor for
// a business" call reaches the network (the Cloudflare Worker), so tailoring is
// the one resume feature that needs a connection.
const CACHE = "lolo-job-hunt-v4";
const SHELL = ["./", "./index.html", "./resume.html", "./resume.baseline.json"];

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
  const path = new URL(event.request.url).pathname;
  // The baseline resume rides along with the shell: the editor fetches it on
  // every load, so without it here a Home Screen launch with no signal would
  // fail that request instead of falling back to the last deployed copy.
  const isAppShell =
    event.request.mode === "navigate" ||
    /\/(index\.html|resume\.html|resume\.baseline\.json)$/.test(path);
  if (!isAppShell) return;
  event.respondWith(
    fetch(event.request)
      .then((res) => {
        const clone = res.clone();
        caches.open(CACHE).then((c) => c.put(event.request, clone));
        return res;
      })
      .catch(() =>
        caches.match(event.request).then((res) => {
          if (res) return res;
          // A missing baseline must read as a failed fetch, not as a page:
          // handing HTML back to the editor's JSON.parse would look like a
          // corrupt baseline rather than "you're offline, keep your edits".
          if (path.endsWith("resume.baseline.json")) return Response.error();
          // Otherwise only ever substitute the jobs page for a jobs URL —
          // handing back index.html for resume.html would silently lose the
          // page the resume editor lives on.
          return caches.match(path.endsWith("resume.html") ? "./resume.html" : "./index.html");
        })
      )
  );
});
