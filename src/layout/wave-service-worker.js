const CACHE_NAME = __WAVE_CACHE_NAME__;
const CACHE_PREFIX = "wave-motions-";
const PRECACHE_URLS = __WAVE_PRECACHE_URLS__;
const precacheRequests = PRECACHE_URLS.map(
  (url) => new Request(url, { cache: "reload" }),
);

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(precacheRequests))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key.startsWith(CACHE_PREFIX) && key !== CACHE_NAME)
          .map((key) => caches.delete(key)),
      ).then(() => self.clients.claim()),
    ),
  );
});

const scopeUrl = new URL(self.registration.scope);
const assetRootPath = new URL("assets/", scopeUrl).pathname;
const readerPagePattern = /(?:^|\/)(?:index|chapter\d+|references)\.html$/;
const readerPageQuery = (url) =>
  Boolean(url.search) &&
  (url.pathname === scopeUrl.pathname || readerPagePattern.test(url.pathname));

const cachedRequest = (cache, request, url) => {
  if (url.pathname.startsWith(assetRootPath)) {
    // Build identity is the only query used for cached reader assets.
    return cache.match(request, { ignoreSearch: true });
  }

  if (
    url.pathname === scopeUrl.pathname &&
    (!url.search || readerPageQuery(url))
  ) {
    const indexUrl = new URL(url);
    indexUrl.pathname = scopeUrl.pathname + "index.html";
    indexUrl.search = "";
    return cache.match(indexUrl.href);
  }

  if (readerPageQuery(url)) {
    const pageUrl = new URL(url);
    pageUrl.search = "";
    return cache.match(pageUrl.href);
  }

  return cache.match(request);
};

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (
    url.origin !== scopeUrl.origin ||
    !url.pathname.startsWith(scopeUrl.pathname)
  ) return;

  event.respondWith(
    caches.open(CACHE_NAME).then((cache) => {
      return cachedRequest(cache, request, url).then(
        (cached) => cached || fetch(request),
      );
    }),
  );
});
