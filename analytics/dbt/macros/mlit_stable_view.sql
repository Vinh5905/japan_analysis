{% materialization mlit_stable_view, adapter = "postgres" %}
    {# Keep relation identity: default rename/drop of a view can CASCADE into
     published outputs. MLIT refresh must never drop the serving views. #}
    {% set relation = this.incorporate(type="view") %}
    {{ run_hooks(pre_hooks, inside_transaction=False) }}
    {{ run_hooks(pre_hooks, inside_transaction=True) }}
    {% call statement("main") %}
    create or replace view {{ relation }} as {{ sql }}
    {% endcall %}
    {{ run_hooks(post_hooks, inside_transaction=True) }}
    {{ adapter.commit() }}
    {{ run_hooks(post_hooks, inside_transaction=False) }}
    {{ return({"relations": [relation]}) }}
{% endmaterialization %}
