# -*- coding: utf-8 -*-

"""Functions for filtering the knowledge graph."""

import itertools as itt
from functools import partial
from typing import Iterable, List, Tuple

import pandas as pd

from pybel import BELGraph
from pybel.constants import (
    ACTIVITY, CAUSAL_INCREASE_RELATIONS, CAUSAL_RELATIONS, CITATION, CITATION_REFERENCE, CITATION_TYPE,
    DIRECT_CAUSAL_RELATIONS, EFFECT, EVIDENCE, IDENTIFIER, LINE, MODIFIER, NAME, PMOD_CODE, PMOD_POSITION, RELATION,
    SUBJECT,
)
from pybel.dsl import BaseEntity, Fragment, Gene, Hgvs, Protein, ProteinModification


def get_modifiers(graph: BELGraph, hgnc_gene_symbol: str, only_direct: bool = False) -> pd.DataFrame:
    """Get a data frame with the proteins that modify the given protein and at what position.

    The columns in this data frame are:

    - Namespace
    - Name
    - Contact
    - Polarity
    - Modification type
    - Residue
    - Position
    - Reference
    - Evidence
    """
    rows = list(_get_protein_modifiers_rows(
        graph=graph,
        hgnc_gene_symbol=hgnc_gene_symbol,
        only_direct=only_direct,
    ))

    return pd.DataFrame(rows, columns=[
        'namespace',
        'name',
        'contact',
        'polarity',
        'modification',
        'residue',
        'position',
        'citation_type',
        'reference',
        'evidence',
    ])


def _get_protein_modifiers_rows(
        graph: BELGraph,
        hgnc_gene_symbol: str,
        only_direct: bool = False,
        require_residue: bool = False,
        only_manual: bool = False) -> Iterable[Tuple]:
    """"""
    for source, target, data in graph.edges(data=True):
        if not isinstance(source, Protein) or not isinstance(target, Protein):
            continue
        if target.namespace.lower() != 'hgnc' or target.name != hgnc_gene_symbol:
            continue
        if not target.variants or 1 != len(target.variants):
            continue
        variant = target.variants[0]
        if not isinstance(variant, ProteinModification):
            continue
        if data[RELATION] not in CAUSAL_RELATIONS:
            continue
        if only_direct and data[RELATION] not in DIRECT_CAUSAL_RELATIONS:
            continue
        if require_residue and not (variant.get(PMOD_CODE) and variant.get(PMOD_POSITION)):
            continue

        automatic = 'INDRA_UUID' in data or data.get(LINE) == 0
        if only_manual and automatic:
            continue

        yield (
            source.namespace,
            # source.identifier,
            source.name,
            data[RELATION] in DIRECT_CAUSAL_RELATIONS,
            data[RELATION] in CAUSAL_INCREASE_RELATIONS,
            variant[IDENTIFIER][NAME],
            variant.get(PMOD_CODE),
            variant.get(PMOD_POSITION),
            data[CITATION][CITATION_TYPE],
            data[CITATION][CITATION_REFERENCE],
            data[EVIDENCE],
            automatic,
        )


get_tau_modifiers = partial(get_modifiers, hgnc_gene_symbol='MAPT')


def get_kinases(graph: BELGraph, only_direct: bool = False) -> pd.DataFrame:
    """Get a data frame with the proteins that are acting as kinases.

    The columns in this data frame are:

    1. Namespace
    2. Name
    3. References
    """
    rows = list(get_kinases_rows(graph))

    return pd.DataFrame(rows, columns=[
        'namespace',
        'name',
        'reference',
    ])


def get_kinases_rows(graph: BELGraph) -> Iterable[Tuple]:
    """"""
    for source, _, data in graph.edges(data=True):
        if not isinstance(source, Protein):
            continue
        subject_activity = data.get(SUBJECT)
        if subject_activity is None:
            continue
        if MODIFIER not in subject_activity:
            continue
        if subject_activity[MODIFIER] != ACTIVITY:
            continue
        if EFFECT not in subject_activity:
            continue
        if subject_activity[EFFECT][NAME] != 'kin':
            continue

        yield (
            source.namespace,
            source.name,
            data[CITATION][CITATION_REFERENCE],
        )


def get_variants_rows(graph: BELGraph, hgnc_gene_symbol: str) -> Iterable[Tuple]:
    """"""
    for node in graph:
        if not is_hgnc_protein(node, hgnc_gene_symbol):
            continue
        if not node.variants or 1 != len(node.variants):
            continue
        variant = node.variants[0]
        if not isinstance(variant, Hgvs):
            continue

        yield (
            node.namespace,
            node.name,
            variant[IDENTIFIER],
            get_all_references(graph, node),
        )


def get_fragments_rows(graph: BELGraph, hgnc_gene_symbol: str) -> Iterable[Tuple]:
    """"""
    for node in graph:
        if not is_hgnc_protein(node, hgnc_gene_symbol):
            continue
        if not node.variants or 1 != len(node.variants):
            continue
        variant = node.variants[0]
        if not isinstance(variant, Fragment):
            continue

        yield (
            node.namespace,
            node.name,
            variant.range,
            get_all_references(graph, node),
        )


def is_hgnc_protein(node: BaseEntity, hgnc_gene_symbol) -> bool:
    return isinstance(node, Protein) and node.namespace.lower() == 'hgnc' and node.name == hgnc_gene_symbol


def get_mutations_rows(graph: BELGraph, hgnc_gene_symbol: str) -> Iterable[Tuple]:
    """"""
    for node in graph:
        if not isinstance(node, Gene):
            continue
        if node.namespace.lower() != 'hgnc' or node.name != hgnc_gene_symbol:
            continue
        if not node.variants or 1 != len(node.variants):
            continue
        variant = node.variants[0]
        if not isinstance(variant, Hgvs):
            continue

        yield (
            node.namespace,
            node.name,
            variant[IDENTIFIER],
            get_all_references(graph, node),
        )


def get_all_references(graph: BELGraph, node):
    return list(sorted(set(
        (
            data[CITATION][CITATION_TYPE],
            data[CITATION][CITATION_REFERENCE],
        )
        for _, _, data in itt.chain(graph.in_edges(node, data=True), graph.out_edges(node, data=True))
        if CITATION in data
    )))


def get_tau_references(graph: BELGraph, hgnc_gene_symbol='MAPT') -> List[Tuple[str, str]]:
    """Get a list of references that contain the Tau protein."""
    return list(sorted(set(
        (
            data[CITATION][CITATION_TYPE],
            data[CITATION][CITATION_REFERENCE],
        )
        for source, target, data in graph.edges(data=True)
        if (
                CITATION in data and data.get(LINE) and
                (is_hgnc_protein(source, hgnc_gene_symbol) or is_hgnc_protein(target, hgnc_gene_symbol))
        )
    )))


AGGREGATION_TERM_DICT = {
    'HBP00006': 'Tau aggregates',
    'HBP00100': 'paired helical filaments',
    'HBP00101': 'straight filaments',
}
AGGREGATION_TERMS = set(itt.chain.from_iterable(AGGREGATION_TERM_DICT.items()))


def get_tau_aggregation_modifiers_rows(
        graph: BELGraph,
        only_direct: bool = False) -> Iterable[Tuple]:
    """"""
    for source, target, data in graph.edges(data=True):
        if not isinstance(source, Protein) or not isinstance(target, Protein):
            continue
        if target.namespace.lower() != 'hbp' or target.name not in AGGREGATION_TERMS:
            continue
        if data[RELATION] not in CAUSAL_RELATIONS:
            continue
        if only_direct and data[RELATION] not in DIRECT_CAUSAL_RELATIONS:
            continue

        yield (
            source.namespace,
            # source.identifier,
            source.name,
            target.name,
            data[CITATION][CITATION_TYPE],
            data[CITATION][CITATION_REFERENCE],
            data[EVIDENCE],
        )


def get_edges(
        graph: BELGraph,
        hgnc_gene_symbol: str = 'MAPT',
) -> Iterable[Tuple[str, str, str]]:
    for source, target, data in graph.edges(data=True):
        if CITATION not in data:
            continue
        if is_hgnc_protein(source, hgnc_gene_symbol) or is_hgnc_protein(target, hgnc_gene_symbol):
            yield (
                graph.edge_to_bel(source, target, data, sep=' '),
                data[CITATION][CITATION_TYPE],
                data[CITATION][CITATION_REFERENCE]
            )
