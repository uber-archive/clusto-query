# Copyright (c) 2013-2015, Uber, Inc.
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import collections
from clusto import ENTITY_TABLE, ATTR_TABLE, SESSION

from sqlalchemy import select, and_


# ## BACKPORT FROM CLUSTO 0.7.8 ## #
# TODO: delete me after 0.7.8 is widely-deployed

Adjacency = collections.namedtuple(
    'Adjacency',
    ['parent_id', 'parent_name', 'parent_type', 'child_id', 'child_name', 'child_type']
)


def adjacency_map():
    """Return the entire adjacency map of clusto in one pass (all parent/child relationships)

    Returns a list of namedtuples
    """
    parent_entities = ENTITY_TABLE.alias()
    child_entities = ENTITY_TABLE.alias()
    entity_attrs = ATTR_TABLE
    query = select([
        parent_entities.c.entity_id,
        parent_entities.c.name,
        parent_entities.c.type,
        child_entities.c.entity_id,
        child_entities.c.name,
        child_entities.c.type
    ]).select_from(
        entity_attrs.
        join(parent_entities,
             parent_entities.c.entity_id == entity_attrs.c.entity_id).
        join(child_entities,
             child_entities.c.entity_id == entity_attrs.c.relation_id)
    ).where(
        and_(
            entity_attrs.c.deleted_at_version == None,
            child_entities.c.deleted_at_version == None,
            parent_entities.c.deleted_at_version == None,
            entity_attrs.c.key == '_contains',
        )
    )

    res = []
    for row in SESSION.execute(query):
        res.append(Adjacency(*row))
    return res
