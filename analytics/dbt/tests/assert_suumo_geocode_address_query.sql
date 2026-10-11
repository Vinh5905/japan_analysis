-- Shared scenarios with Python/notebook: NFKC, numeric suffix and missing levels.
with
    scenarios(prefecture, district, municipality, ward, locality, chome, expected) as (
        values
            ('大阪府', null, '大阪市', '淀川区', '東三国', '２', '大阪府大阪市淀川区東三国2丁目'),
            (' 大阪府 ', null, '大阪市', '淀川区', '西宮原', '1.0', '大阪府大阪市淀川区西宮原1丁目'),
            ('大阪府', null, '大阪市', null, '西宮原', null, null),
            (null, null, '大阪市', '淀川区', '西宮原', '1', null),
            ('北海道', '虻田郡', '倶知安町', null, '北一条東', '1', '北海道虻田郡倶知安町北一条東1丁目'),
            ('大阪府', '', '大阪市', '淀川区', '西宮原', '0', null),
            ('大阪府', '', '大阪市', '淀川区', '西宮原', '1.5', null)
    )
select *, {{ suumo_geocode_address_query("s") }} as actual
from scenarios s
where ({{ suumo_geocode_address_query("s") }}) is distinct from expected
