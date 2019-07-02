# -*- coding: utf-8 -*-

"""Graph getting functions."""

import logging

import epilepsy_knowledge
import hbp_enrichment
import hbp_knowledge
import hbp_semi_automated_curation
import neurommsig_alzheimers_knowledge
import neurommsig_parkinsons_knowledge
from pybel import BELGraph, union

__all__ = [
    'get_graph',
]

logger = logging.getLogger(__name__)


def get_graph() -> BELGraph:
    """Get the graph from all sources."""
    graphs = []

    logger.info('getting pharmacome/knowledge')
    hbp_graph = hbp_knowledge.get_graph()
    graphs.append(hbp_graph)

    logger.info('getting pharmacome/semi-automated-curation')
    hbp_semi_automated_graph = hbp_semi_automated_curation.repository.get_graph()
    graphs.append(hbp_semi_automated_graph)

    logger.info('getting pharmacome/knowledge')
    hbp_enrichment_graph = hbp_enrichment.repository.get_graph()
    graphs.append(hbp_enrichment_graph)

    return union(graphs)


def get_neurommsig_graph():
    graphs = []
    logger.info('getting neurommsig-epilepsy/knowledge')
    neurommsig_epilepsy_graph = epilepsy_knowledge.repository.get_graph()
    graphs.append(neurommsig_epilepsy_graph)

    try:
        neurommsig_alzheimers_graph = neurommsig_alzheimers_knowledge.repository.get_graph()
    except ImportError:
        logger.info('skipping neurommsig-alzheimers')
    else:
        graphs.append(neurommsig_alzheimers_graph)

    try:
        neurommsig_parkinsons_graph = neurommsig_parkinsons_knowledge.repository.get_graph()
    except ImportError:
        logger.info('skipping neurommsig-parkinsons')
    else:
        graphs.append(neurommsig_parkinsons_graph)

    return union(graphs)
