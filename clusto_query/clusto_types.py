import clusto

# all types known to clusto
CLUSTO_TYPES = set(clusto.TYPELIST.keys()) - set(['clustometa'])

# types which should be recursively searched to build parent/child relationships
CONTEXT_TYPES = set(
    k
    for k in CLUSTO_TYPES
    if (
        'server' not in k and
        k != 'generic' and
        k != 'appliance' and
        k != 'resourcemanger'
    )
)
