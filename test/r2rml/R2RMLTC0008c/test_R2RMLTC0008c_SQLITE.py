__author__ = "Julián Arenas-Guerrero"
__credits__ = ["Julián Arenas-Guerrero"]

__license__ = "Apache-2.0"
__maintainer__ = "Julián Arenas-Guerrero"
__email__ = "arenas.guerrero.julian@outlook.com"


import os
import morph_kgc

from rdflib.graph import Graph
from rdflib import compare


def test_R2RMLTC0008c():
    g = Graph()
    g.parse(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'output.nq'))

    mapping_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'mapping.ttl')
    db_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resource.db')
    config = f'[CONFIGURATION]\ninfer_sql_datatypes=yes\noutput_format=N-QUADS\n[DataSource]\nmappings={mapping_path}\ndb_url=sqlite:///{db_path}'
    g_morph = morph_kgc.materialize(config)

    assert compare.isomorphic(g, g_morph)
