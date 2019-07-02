# -*- coding: utf-8 -*-

""""""

import hbp_knowledge
import hbp_enrichment
import neurommsig_alzheimers_knowledge
import neurommsig_parkinsons_knowledge
import epilepsy_knowledge
import hbp_semi_automated_curation
import logging
from pybel import BELGraph, union

__all__ = [
    'get_graph',
]

logger = logging.getLogger(__name__)


def get_graph() -> BELGraph:
    """Get the graph from all sources."""
    logger.info('getting HBP')
    hbp_graph = hbp_knowledge.get_graph()
    hbp_semi_automated_graph = hbp_semi_automated_curation.repository.get_graph()
    hbp_enrichment_graph = hbp_enrichment.repository.get_graph()

    logger.info('getting NeuroMMSig')
    neurommsig_alzheimers_graph = neurommsig_alzheimers_knowledge.repository.get_graph()
    neurommsig_parkinsons_graph = neurommsig_parkinsons_knowledge.repository.get_graph()
    neurommsig_epilepsy_graph = epilepsy_knowledge.repository.get_graph()

    return union([
        hbp_graph,
        hbp_semi_automated_graph,
        hbp_enrichment_graph,
        neurommsig_alzheimers_graph,
        neurommsig_parkinsons_graph,
        neurommsig_epilepsy_graph,
    ])
