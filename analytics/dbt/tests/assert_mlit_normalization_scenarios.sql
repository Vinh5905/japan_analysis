{{ config(tags=["mlit_zoning_core"]) }}
with
    examples(raw, expected) as (
        values
            ('４００％', 400::numeric),
            (' 200 ', 200::numeric),
            (null, null::numeric),
            ('', null::numeric),
            ('unknown', null::numeric),
            ('400abc', null::numeric)
    ),
    parsed as (select *,{{ mlit_percent("raw") }} as actual from examples)
select raw
from parsed
where actual is distinct from expected
union all
select 'invalid geometry accepted'
where st_isvalid(st_geomfromtext('POLYGON((0 0,1 1,0 1,1 0,0 0))', 6668))
