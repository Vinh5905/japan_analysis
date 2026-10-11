Derived from shiwaku/mlit-urban-planning-converter, MIT, Copyright (c) 2026 Yohei Shiwaku.
Pinned upstream commit: b7cae65868abaf90f2c89e609ea5ed2ef466882e.
Only prefecture GeoJSON URL discovery and Reiwa date parsing are adapted from src/tosiko_pmtiles/scrape.py.
Changes: MLIT-only URL validation, metadata discovery, stdlib HTTP retry,
content hashes instead of content-ID freshness; archive validation and loading are project code.
No upstream CLI, destructive directory cleanup, PMTiles, or simplification is included.
