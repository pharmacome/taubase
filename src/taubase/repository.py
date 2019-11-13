# -*- coding: utf-8 -*-

"""Graph getting functions."""

import logging
import os
from functools import partial

import hbp_enrichment
import hbp_knowledge
import hbp_semi_automated_curation
from pybel import union

from .drepo import DistributedRepo
from .version import VERSION

__all__ = [
    'DistributedRepo',
    'repository',
    'get_graph',
]

logger = logging.getLogger(__name__)

HERE = os.path.abspath(os.path.dirname(__file__))
DATA_DIRECTORY = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir, 'data'))

repository = DistributedRepo(
    name='TauBase',
    version=VERSION,
    directory=DATA_DIRECTORY,
    repositories=[
        hbp_knowledge.repository,
        hbp_semi_automated_curation.repository,
        hbp_enrichment.repository,
    ],
)

get_graph = repository.get_graph


def get_neurommsig_graph():
    graphs = []

    import epilepsy_knowledge
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
