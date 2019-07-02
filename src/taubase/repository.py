# -*- coding: utf-8 -*-

"""Graph getting functions."""

import logging
import os
import pickle

import epilepsy_knowledge
import hbp_enrichment
import hbp_knowledge
import hbp_semi_automated_curation
import pybel
from pybel import BELGraph, union
from pybel_cx import to_cx_file

__all__ = [
    'get_graph',
]

logger = logging.getLogger(__name__)

HERE = os.path.abspath(os.path.dirname(__file__))
DATA_DIRECTORY = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir, 'data'))

PICKLE_PATH = os.path.join(DATA_DIRECTORY, 'taubase.bel.pickle')
NODELINK_PATH = os.path.join(DATA_DIRECTORY, 'taubase.bel.nodelink.json')
CX_PATH = os.path.join(DATA_DIRECTORY, 'taubase.bel.cx.json')
SIF_PATH = os.path.join(DATA_DIRECTORY, 'taubase.bel.sif')
GRAPHML_PATH = os.path.join(DATA_DIRECTORY, 'taubase.bel.graphml')
GSEA_PATH = os.path.join(DATA_DIRECTORY, 'taubase.bel.gmt')
INDRA_PATH = os.path.join(DATA_DIRECTORY, 'taubase.indra.pickle')


def get_graph() -> BELGraph:
    """Get the graph from all sources."""
    if os.path.exists(PICKLE_PATH):
        return pybel.from_pickle(PICKLE_PATH)

    graphs = []

    logger.info('getting pharmacome/knowledge')
    hbp_graph = hbp_knowledge.get_graph(use_tqdm=True)
    graphs.append(hbp_graph)

    logger.info('getting pharmacome/semi-automated-curation')
    hbp_semi_automated_graph = hbp_semi_automated_curation.repository.get_graph(use_tqdm=True)
    graphs.append(hbp_semi_automated_graph)

    logger.info('getting bel-enrichment/results')
    hbp_enrichment_graph = hbp_enrichment.repository.get_graph(use_tqdm=True)
    graphs.append(hbp_enrichment_graph)

    rv = union(graphs)

    pybel.to_pickle(rv, PICKLE_PATH)
    pybel.to_json_path(rv, NODELINK_PATH)
    with open(CX_PATH, 'w') as file:
        to_cx_file(rv, file)
    pybel.to_sif_path(rv, SIF_PATH)
    pybel.to_gsea_path(rv, GSEA_PATH)
    pybel.to_graphml(rv, GRAPHML_PATH)
    try:
        statements = pybel.to_indra_statements(rv)
    except ImportError:
        pass
    else:
        with open(INDRA_PATH, 'wb') as file:
            pickle.dump(statements, file)

    return rv


def get_neurommsig_graph():
    graphs = []
    logger.info('getting neurommsig-epilepsy/knowledge')
    neurommsig_epilepsy_graph = epilepsy_knowledge.repository.get_graph()
    graphs.append(neurommsig_epilepsy_graph)

    try:
        import neurommsig_alzheimers_knowledge
    except ImportError:
        logger.info('skipping neurommsig-alzheimers')
    else:
        neurommsig_alzheimers_graph = neurommsig_alzheimers_knowledge.repository.get_graph()
        graphs.append(neurommsig_alzheimers_graph)

    try:
        import neurommsig_parkinsons_knowledge
    except ImportError:
        logger.info('skipping neurommsig-parkinsons')
    else:
        neurommsig_parkinsons_graph = neurommsig_parkinsons_knowledge.repository.get_graph()
        graphs.append(neurommsig_parkinsons_graph)

    return union(graphs)
