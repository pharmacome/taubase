# -*- coding: utf-8 -*-

"""Graph getting functions."""

import logging
import os
import pickle
from typing import List, Union

import hbp_enrichment
import hbp_knowledge
import hbp_semi_automated_curation
import pybel
from bel_enrichment import BELSheetsRepository
from bel_repository import BELMetadata, BELRepository
from bel_repository.utils import serialize_authors
from pybel import BELGraph, union

__all__ = [
    'DistributedRepo',
    'repo',
    'get_graph',
]

logger = logging.getLogger(__name__)

HERE = os.path.abspath(os.path.dirname(__file__))
DATA_DIRECTORY = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir, 'data'))


class DistributedRepo:
    def __init__(
            self,
            *,
            name,
            repositories: List[Union[BELRepository, BELSheetsRepository]],
            cache_dir,
    ) -> None:
        self.name = name
        self.repositories = repositories

        for r in self.repositories:
            if not hasattr(r, 'metadata'):
                raise TypeError(f'Missing metadata: {r}')


        #
        self.version = '/'.join(
            repository.metadata.version
            for repository in self.repositories
        )
        self.authors = serialize_authors({
            author.strip()
            for repository in self.repositories
            for author in repository.metadata.authors.split(',')
        })
        self.description = """A distributed repository of several repositories: {}""".format(
            f'{repository.metadata.name} v{repository.metadata.version}' for repository in self.repositories
        )
        self.metadata = BELMetadata(
            name=self.name,
            version=self.version,
            authors=self.authors,
            description=self.description,
        )
        self.cache_dir = cache_dir

    def get_graphs(self, use_tqdm: bool = True):
        return [
            repository.get_graph(use_tqdm=use_tqdm)
            for repository in self.repositories
        ]

    def get_graph(self, use_cached: bool = True) -> BELGraph:
        """Get the graph from all sources."""
        pickle_path = os.path.join(self.cache_dir, 'taubase.bel.pickle')
        if use_cached and os.path.exists(pickle_path):
            return pybel.from_pickle(pickle_path)

        rv = union(self.get_graphs())
        self.metadata.update(rv)

        nodelink_path = os.path.join(self.cache_dir, f'{self.name}.bel.nodelink.json')
        cx_path = os.path.join(self.cache_dir, f'{self.name}.bel.cx.json')
        sif_path = os.path.join(self.cache_dir, f'{self.name}.bel.sif')
        graphml_path = os.path.join(self.cache_dir, f'{self.name}.bel.graphml')
        gsea_path = os.path.join(self.cache_dir, f'{self.name}.bel.gmt')
        indra_path = os.path.join(self.cache_dir, f'{self.name}.indra.pickle')
        html_path = os.path.join(self.cache_dir, 'index.html')

        pybel.to_pickle(rv, pickle_path)
        pybel.to_json_path(rv, nodelink_path)
        pybel.to_sif_path(rv, sif_path)
        pybel.to_gsea_path(rv, gsea_path)
        pybel.to_graphml(rv, graphml_path)

        try:
            statements = pybel.to_indra_statements(rv)
        except ImportError:
            pass
        else:
            with open(indra_path, 'wb') as file:
                pickle.dump(statements, file)

        try:
            from pybel_cx import to_cx_file
        except ImportError:
            pass
        else:
            with open(cx_path, 'w') as file:
                to_cx_file(rv, file)

        try:
            from pybel_tools.assembler.html import to_html
        except ImportError:
            pass
        else:
            with open(html_path, 'w') as file:
                print(to_html(rv), file=file)

        return rv


repo = DistributedRepo(
    name='TauBase',
    repositories=[
        hbp_knowledge.repository,
        hbp_semi_automated_curation.repository,
        hbp_enrichment.repository,
    ],
    cache_dir=DATA_DIRECTORY,
)

get_graph = repo.get_graph


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
