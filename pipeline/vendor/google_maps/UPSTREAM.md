# Vendored Google Maps search protocol

- Source: https://github.com/sonagara-vashram/google-maps-scraper
- Commit: `3d01d6c5ee23cc5a0dcf088b6d379fb107a51908`
- Copyright (c) 2026 Sonagara Vasram; MIT, see LICENSE.
- Derived portions: text-search pb/URL templates and place JSON record detection/field indices from `constants.py` and `parser.py`.
- Local changes: only name/address/point/place identity fields; structured JSON required; reject non-finite JSON literals; keep duplicates for ambiguity checking; no regex fallback, browser, grid, reviews, email, proxy pool, CLI or SQLite.
- HTTP/TLS, matching, throttling and warehouse persistence are project-owned in the building locator. TLS verification is enabled.
- Upstream code license does not license Google Maps data. No automatic upstream download/update at runtime.
