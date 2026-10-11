BEGIN;
CREATE TABLE IF NOT EXISTS crawl_area_catalogs (
    source_id BIGINT NOT NULL REFERENCES crawl_sources (source_id),
    scope TEXT NOT NULL, catalog_url TEXT NOT NULL,
    synced_at TIMESTAMPTZ, PRIMARY KEY (source_id, scope)
);
CREATE TABLE IF NOT EXISTS crawl_areas (
    area_id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL REFERENCES crawl_sources (source_id),
    prefecture TEXT NOT NULL, district TEXT, municipality TEXT NOT NULL,
    ward TEXT NOT NULL,
    display_name TEXT NOT
    NULL,
    sc TEXT NOT NULL CHECK
    (sc ~ '^[0-9]{5}$'),
    UNIQUE (source_id, prefecture, municipality, ward),
    UNIQUE (source_id, sc) DEFERRABLE INITIALLY DEFERRED
);
ALTER TABLE crawl_runs ADD COLUMN IF NOT EXISTS area_id BIGINT REFERENCES crawl_areas (
    area_id
);
ALTER TABLE crawl_runs ADD COLUMN IF NOT EXISTS pipeline_key TEXT UNIQUE;
ALTER TABLE crawl_runs ADD COLUMN IF NOT EXISTS search_url TEXT;
ALTER TABLE crawl_runs ADD COLUMN IF NOT EXISTS area_snapshot JSONB;
ALTER TABLE crawl_runs ADD COLUMN IF NOT EXISTS pipeline_status TEXT CHECK (
    pipeline_status IN
    (
        'running',
        'completed',
        'preflight_failed',
        'crawl_failed',
        'cleanup_failed',
        'interrupted'
    )
);
ALTER TABLE crawl_runs ADD COLUMN IF NOT EXISTS pipeline_finished_at TIMESTAMPTZ;
ALTER TABLE crawl_runs ADD COLUMN IF NOT EXISTS cleanup_confirmed_at TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS idx_crawl_runs_area_created ON crawl_runs (
    area_id, created_at DESC
);
INSERT INTO crawl_areas (source_id, prefecture, municipality, ward, display_name, sc)
SELECT
    s.source_id,
    '大阪府',
    '大阪市',
    v.ward,
    v.name,
    v.sc
FROM crawl_sources s CROSS JOIN (
    VALUES
    ('都島区', 'Miyakojima', '27102'),
    ('福島区', 'Fukushima', '27103'),
    ('此花区', 'Konohana', '27104'),
    ('西区', 'Nishi', '27106'),
    ('港区', 'Minato', '27107'),
    ('大正区', 'Taisho', '27108'),
    ('天王寺区', 'Tennoji', '27109'),
    ('浪速区', 'Naniwa', '27111'),
    ('西淀川区', 'Nishiyodogawa', '27113'),
    ('東淀川区', 'Higashiyodogawa', '27114'),
    ('東成区', 'Higashinari', '27115'),
    ('生野区', 'Ikuno', '27116'),
    ('旭区', 'Asahi', '27117'),
    ('城東区', 'Joto', '27118'),
    ('阿倍野区', 'Abeno', '27119'),
    ('住吉区', 'Sumiyoshi', '27120'),
    ('東住吉区', 'Higashisumiyoshi', '27121'),
    ('西成区', 'Nishinari', '27122'),
    ('淀川区', 'Yodogawa', '27123'),
    ('鶴見区', 'Tsurumi', '27124'),
    ('住之江区', 'Suminoe', '27125'),
    ('平野区', 'Hirano', '27126'),
    ('北区', 'Kita', '27127'),
    ('中央区', 'Chuo', '27128')
) v (ward, name, sc)
WHERE s.source_key = 'suumo'
ON CONFLICT (source_id, prefecture, municipality, ward) DO NOTHING;
-- Confirmed legacy SUUMO scope: Yodogawa. Do not infer old pipeline results.
UPDATE crawl_runs r SET
    area_id = a.area_id,
    area_snapshot = jsonb_build_object(
        'prefecture', a.prefecture, 'district', a.district,
        'municipality',
        a.municipality,
        'ward',
        a.ward,
        'display_name',
        a.display_name,
        'sc',
        a.sc,
        'area_id',
        a.area_id
    )
FROM crawl_areas a JOIN crawl_sources s ON s.source_id = a.source_id
WHERE
    r.source_id = s.source_id AND s.source_key = 'suumo' AND a.ward = '淀川区'
    AND r.area_id IS NULL AND r.pipeline_key IS NULL;
INSERT INTO crawl_area_catalogs (source_id, scope, catalog_url)
SELECT
    source_id,
    'osaka_city',
    'https://suumo.jp/chintai/osaka/city/'
FROM crawl_sources
WHERE source_key = 'suumo'
ON CONFLICT DO NOTHING;
COMMIT;
