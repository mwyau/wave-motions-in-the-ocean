import json
import re
import urllib.parse
from pathlib import Path

import validate
from publication import BOOK_TITLE, PUBLICATION_TITLE, SITE_URL, SRC, BuildInfo
from webapp import (
    APPLE_TOUCH_ICON_PATH,
    ARTWORK_ASSET_PATHS,
    MANIFEST_ICON_OUTPUTS,
    OFFLINE_EXCLUDED_ASSETS,
    SERVICE_WORKER_FILENAME,
    WEB_APP_NAME,
    WEB_APP_SHORT_NAME,
    WEB_MANIFEST_FILENAME,
    all_reader_resources,
    generate_application_icons,
    offline_reader_resources,
    reader_palette,
    service_worker_text,
    web_app_manifest_text,
    write_service_worker,
    write_web_app_manifest,
)


def precache_entries(worker: str) -> list[str]:
    match = re.search(
        r"const\s+PRECACHE_URLS\s*=\s*(\[.*?\]);", worker, flags=re.DOTALL
    )
    assert match is not None
    return json.loads(match.group(1))


def test_web_app_manifest_is_deterministic_and_pages_safe() -> None:
    first = web_app_manifest_text()
    assert first == web_app_manifest_text()
    manifest = json.loads(first)

    assert PUBLICATION_TITLE == f"{BOOK_TITLE}: Myrl's View"
    assert manifest["name"] == WEB_APP_NAME == BOOK_TITLE == "Wave Motions in the Ocean"
    assert manifest["short_name"] == WEB_APP_SHORT_NAME == "Wave Motions"
    assert manifest["name"] != manifest["short_name"]
    assert all("Myrl's View" not in manifest[key] for key in ("name", "short_name"))
    assert manifest["id"] == manifest["start_url"] == manifest["scope"] == "./"
    assert manifest["display"] == "standalone"
    assert manifest["lang"] == "en-US"
    assert manifest["background_color"] == reader_palette()[0]
    assert manifest["theme_color"] == reader_palette()[1]
    assert [entry["sizes"] for entry in manifest["icons"]] == [
        f"{size}x{size}" for _name, size in MANIFEST_ICON_OUTPUTS
    ]
    assert all(
        entry["type"] == "image/png" and entry["purpose"] == "any maskable"
        for entry in manifest["icons"]
    )

    manifest_url = f"{SITE_URL}/{WEB_MANIFEST_FILENAME}"
    resolved_scope = urllib.parse.urljoin(manifest_url, manifest["scope"])
    assert resolved_scope == f"{SITE_URL}/"
    assert all(
        urllib.parse.urljoin(manifest_url, entry["src"]).startswith(
            f"{SITE_URL}/assets/icons/"
        )
        for entry in manifest["icons"]
    )


def test_service_worker_registration_is_guarded_and_repository_safe() -> None:
    source = (SRC / "layout" / "wave-html.js").read_text()

    assert '"serviceWorker" in navigator' in source
    assert (
        'navigator.serviceWorker\n    .register("./service-worker.js", { scope: "./" })'
        in source
    )
    assert "window.isSecureContext" in source
    assert 'location.protocol === "http:"' in source
    assert 'location.protocol === "https:"' in source
    assert (
        "const hadController = navigator.serviceWorker.controller !== null;" in source
    )
    assert "let reloadingForUpdate = false;" in source
    assert "if (hadController)" in source
    assert 'navigator.serviceWorker.addEventListener("controllerchange"' in source
    assert "if (reloadingForUpdate) return;" in source
    assert "reloadingForUpdate = true;" in source
    assert "location.reload();" in source


def test_service_worker_has_sorted_complete_precache_and_versioned_lifecycle(
    tmp_path: Path,
) -> None:
    root = tmp_path / "release"
    (root / "assets" / "fonts").mkdir(parents=True)
    for name in ("index.html", "chapter1.html", "references.html"):
        (root / name).write_text(name)
    (root / WEB_MANIFEST_FILENAME).write_text(web_app_manifest_text())
    for name in (
        "wave.css",
        "wave.js",
        "fonts/reader.woff2",
        "mathjax/tex-chtml-full.js",
        "mathjax/output/chtml/fonts/woff-v2/MathJax_Main-Regular.woff",
        "figures/scientific-vector.svg",
        "figures/scientific-original.png",
        "figures/great-wave-met-dp130155.jpg",
        "figures/naruto-whirlpool-met-jp1198.jpg",
        "figures/salmon-hendershott-como-1980.jpg",
        "figures/small-publication.jpeg",
        "icons/icon-192.png",
        "icons/icon-512.png",
        "icons/apple-touch-icon.png",
    ):
        path = root / "assets" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(name.encode())
    for name in (
        "wave-motions.pdf",
        "wave-motions.epub",
        "wave-motions-html.zip",
        "SHA256SUMS",
        "assets/ignored.pdf",
        "assets/SHA256SUMS",
        "assets/service-worker.js",
    ):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"excluded")

    info = BuildInfo("a" * 40, "abcdef0", None)
    worker = service_worker_text(root, info)
    entries = precache_entries(worker)

    assert entries == list(offline_reader_resources(root))
    assert entries == sorted(entries)
    assert set(entries) == set(all_reader_resources(root)) - set(ARTWORK_ASSET_PATHS)
    assert set(ARTWORK_ASSET_PATHS) == set(OFFLINE_EXCLUDED_ASSETS)
    assert set(ARTWORK_ASSET_PATHS).isdisjoint(entries)
    assert {
        "assets/wave.css",
        "assets/wave.js",
        "assets/fonts/reader.woff2",
        "assets/mathjax/tex-chtml-full.js",
        "assets/mathjax/output/chtml/fonts/woff-v2/MathJax_Main-Regular.woff",
        "assets/figures/scientific-vector.svg",
        "assets/figures/scientific-original.png",
        "assets/figures/salmon-hendershott-como-1980.jpg",
        "assets/figures/small-publication.jpeg",
        "assets/icons/icon-192.png",
        "assets/icons/icon-512.png",
        "assets/icons/apple-touch-icon.png",
    } <= set(entries)
    assert all(
        not entry.lower().endswith((".pdf", ".epub", ".zip")) for entry in entries
    )
    assert "SHA256SUMS" not in entries
    assert SERVICE_WORKER_FILENAME not in entries
    assert "assets/SHA256SUMS" not in entries
    assert "assets/service-worker.js" not in entries
    assert set(ARTWORK_ASSET_PATHS).isdisjoint(precache_entries(worker))
    assert 'const CACHE_NAME = "wave-motions-abcdef0";' in worker
    assert 'const CACHE_PREFIX = "wave-motions-";' in worker
    assert "self.skipWaiting()" in worker
    assert "self.clients.claim()" in worker
    assert worker.index("cache.addAll(PRECACHE_URLS)") < worker.index(
        "self.skipWaiting()"
    )
    assert worker.index("caches.delete") < worker.index("self.clients.claim()")
    assert "cache.put" not in worker
    assert "isRuntimeFigure" not in worker


def test_pwa_validator_accepts_a_generated_publication_root(
    tmp_path: Path, monkeypatch
) -> None:
    root = tmp_path / "release"
    root.mkdir()
    generate_application_icons(root / "assets" / "icons", announce=False)
    for name in ("index.html", "chapter1.html", "references.html"):
        (root / name).write_text(
            '<link rel="manifest" href="app.webmanifest">'
            f'<link rel="apple-touch-icon" sizes="180x180" href="{APPLE_TOUCH_ICON_PATH}">'
        )
    for name in (
        *ARTWORK_ASSET_PATHS,
        "assets/figures/salmon-hendershott-como-1980.jpg",
        "assets/figures/scientific-original.png",
        "assets/figures/scientific-vector.svg",
        "assets/figures/small-publication.jpeg",
    ):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(name.encode())
    write_web_app_manifest(root)
    info = BuildInfo("b" * 40, "bcdef01", None)
    write_service_worker(root, info)
    monkeypatch.setattr(validate, "current_build", lambda: info)

    assert validate.pwa_errors(root) == []
