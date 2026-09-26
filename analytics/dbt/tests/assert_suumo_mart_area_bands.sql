with cases as (
    select * from (values
        (null::numeric, 'unknown'), (-1, 'unknown'), (0, 'unknown'),
        (19.99, '<20'), (20, '20-<30'), (29.99, '20-<30'),
        (30, '30-<40'), (40, '40-<50'), (50, '50-<70'),
        (70, '70-<100'), (99.99, '70-<100'), (100, '>=100')
    ) v(area, expected_band)
)
select * from cases
where {{ suumo_area_band('area') }} is distinct from expected_band
