# -*- coding: utf-8 -*-

"""A distributed repository."""

import os
import pickle
from typing import List, Mapping, Optional, Union

import pybel
from bel_enrichment import BELSheetsRepository
from bel_repository import BELMetadata, BELRepository
from bel_repository.utils import serialize_authors
from pybel import BELGraph, union

__all__ = [
    'DistributedRepo',
]


class DistributedRepo:
    """A repository dependent on several BEL repositories."""

    def __init__(
            self,
            *,
            name: str,
            version: str,
            repositories: List[Union[BELRepository, BELSheetsRepository]],
            directory: Optional[str] = None,
    ) -> None:
        """Initialize a distributed repository.

        :param name: The name of the distributed repository
        :param version: The version of the distributed repository, independent of the constituent
         repositories' versions
        :param repositories: A list of BEL repositories
        """
        self.name = name
        self.repositories = repositories
        self.directory = directory

        for repository in self.repositories:
            if not hasattr(repository, 'metadata'):
                raise TypeError(f'Missing metadata: {repository}')

        self.dependency_version = '/'.join(
            repository.metadata.version
            for repository in self.repositories
        )
        self.version = f'{version} ({self.dependency_version})'
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

    def get_graphs(self, use_tqdm: bool = True) -> Mapping[str, BELGraph]:
        """Get a mapping of all BEL graphs in the repository."""
        return {
            repository.metadata.name: repository.get_graph(use_tqdm=use_tqdm)
            for repository in self.repositories
        }

    def get_graph(
            self,
            directory: Optional[str] = None,
            use_cached: bool = True,
            use_tqdm: bool = True,
    ) -> BELGraph:
        """Get the graph from all sources."""
        if directory is None:
            if self.directory is None:
                raise ValueError
            directory = self.directory

        pickle_path = os.path.join(directory, f'{self.name}.bel.pickle')
        if use_cached and os.path.exists(pickle_path):
            return pybel.from_pickle(pickle_path)

        rv = union(self.get_graphs(use_tqdm=use_tqdm))
        self.metadata.update(rv)

        pybel.to_pickle(rv, pickle_path)

        nodelink_path = os.path.join(directory, f'{self.name}.bel.nodelink.json')
        pybel.to_json_path(rv, nodelink_path)

        sif_path = os.path.join(directory, f'{self.name}.bel.sif')
        pybel.to_sif_path(rv, sif_path)

        gsea_path = os.path.join(directory, f'{self.name}.bel.gmt')
        pybel.to_gsea_path(rv, gsea_path)

        graphml_path = os.path.join(directory, f'{self.name}.bel.graphml')
        pybel.to_graphml(rv, graphml_path)

        try:
            statements = pybel.to_indra_statements(rv)
        except ImportError:
            pass
        else:
            indra_path = os.path.join(directory, f'{self.name}.indra.pickle')
            with open(indra_path, 'wb') as file:
                pickle.dump(statements, file)

        try:
            from pybel_cx import to_cx_file
        except ImportError:
            pass
        else:
            cx_path = os.path.join(directory, f'{self.name}.bel.cx.json')
            with open(cx_path, 'w') as file:
                to_cx_file(rv, file)

        try:
            from pybel_tools.assembler.html import to_html
        except ImportError:
            pass
        else:
            html_path = os.path.join(directory, 'index.html')
            with open(html_path, 'w') as file:
                print(to_html(rv), file=file)

        return rv

    def get_indra_statements(self, directory: str, use_cached: bool = True) -> List['indra.statements.Statement']:
        """Get INDRA statements for the graph."""
        return pybel.to_indra_statements(self.get_graph(directory, use_cached=use_cached))
