// Atemschutzüberwachung – Service Worker
// Ziel: App auch bei fehlendem Internet öffnen können (letzter geladener Stand),
// aber bei vorhandener Verbindung IMMER die neueste Version laden (kein "Steckenbleiben"
// auf einer alten Version bei einem Sicherheits-Tool).

const CACHE_NAME = "atemschutz-cache-v1";
const APP_SHELL = [
  "./",
  "./index.html",
  "./manifest.json",
  "./kapitel12.pdf",
  "./kapitel7.pdf"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(APP_SHELL).catch(() => {
        // Falls einzelne Dateien (z.B. CDN-Skripte) beim Install nicht erreichbar sind,
        // soll die Installation trotzdem nicht fehlschlagen.
      });
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      )
    )
  );
  self.clients.claim();
});

// Network-first: Online -> immer frische Version laden + Cache aktualisieren.
// Offline -> letzte gecachte Version verwenden (App bleibt nutzbar).
self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        const copy = response.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, copy).catch(() => {});
        });
        return response;
      })
      .catch(() => {
        return caches.match(event.request).then((cached) => {
          if (cached) return cached;
          // Bei Navigation ohne Cache-Treffer: Startseite als Fallback versuchen.
          if (event.request.mode === "navigate") {
            return caches.match("./index.html");
          }
          return undefined;
        });
      })
  );
});
