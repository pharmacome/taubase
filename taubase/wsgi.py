# -*- coding: utf-8 -*-

"""Run TauBase."""
import logging
import os
import sys

import neurommsig_knowledge
import pandas as pd
from flask import Flask, jsonify, render_template, request
from flask_bootstrap import Bootstrap

import hbp_knowledge
from pybel import union
from taubase.getters import (
    _get_protein_modifiers_rows, get_fragments_rows, get_kinases, get_mutations_rows,
    get_tau_aggregation_modifiers_rows, get_tau_modifiers, get_tau_references, get_variants_rows, get_edges
)

logger = logging.getLogger(__name__)

logger.info('getting HBP')
hbp_graph = hbp_knowledge.get_graph()

logger.info('getting NeuroMMSig')
neurommsig_graph = neurommsig_knowledge.repository.get_graph()

logger.info('getting HBP Enrichment')
sys.path.append(os.path.join(os.path.expanduser('~'), 'dev', 'hbp-results'))
import hbp_results

enrichment_graph = hbp_results.sheets_repository.get_graph()

logger.info('joining graphs')
graph = union([hbp_graph, neurommsig_graph, enrichment_graph])

app = Flask(__name__)
Bootstrap(app)


def _get_hgnc_gene_symbol():
    return request.args.get('hgnc_gene_symbol', default='MAPT')


@app.route('/')
def home():
    """Show the home page."""
    return render_template('index.html', summary=graph.summary_dict())


@app.route('/summary.json')
def summary_json():
    """Return a summary of the contents of the graphs."""
    return jsonify(graph.summary_dict())


@app.route('/references')
def tau_references():
    """Show the modifiers of the Tau protein."""
    rows = get_tau_references(graph)
    return render_template('references.html', rows=rows)


@app.route('/modifiers')
def tau_modifiers():
    """Show the modifiers of the Tau protein."""
    rows = list(_get_protein_modifiers_rows(
        graph,
        only_direct=request.args.get('only_direct', type=bool, default=True),
        hgnc_gene_symbol=_get_hgnc_gene_symbol(),
        require_residue=request.args.get('require_residue', type=_bool_str, default=True),
        only_manual=request.args.get('only_manual', type=_bool_str, default=False)
    ))

    return render_template('modifiers.html', rows=rows)


def _bool_str(x: str):
    return x.lower() == 'true'


@app.route('/variants')
def tau_variants():
    """Show the variants of the Tau protein."""
    rows = list(get_variants_rows(
        graph=graph,
        hgnc_gene_symbol=_get_hgnc_gene_symbol(),
    ))

    return render_template('variants.html', rows=rows)


@app.route('/mutations')
def tau_mutations():
    """Show the genetic mutations of the Tau protein."""
    rows = list(get_mutations_rows(
        graph=graph,
        hgnc_gene_symbol=_get_hgnc_gene_symbol(),
    ))

    return render_template('variants.html', rows=rows)


@app.route('/fragments')
def tau_fragments():
    """Show the fragments of the Tau protein."""
    rows = list(get_fragments_rows(
        graph=graph,
        hgnc_gene_symbol=_get_hgnc_gene_symbol(),
    ))

    return render_template('fragments.html', rows=rows)


@app.route('/edges')
def edges():
    """Show the edges with the Tau protein."""
    return render_template('edges.html', rows=list(get_edges(graph, _get_hgnc_gene_symbol())))

@app.route('/aggregation/inhibitors')
def tau_aggregation_inhibitors():
    rows = list(get_tau_aggregation_modifiers_rows(graph))
    return render_template('tau_aggregation_inhibitors.html', rows=rows)


"""JSON Endpoints"""


@app.route('/modifiers.json')
def tau_modifiers_json():
    """Show the modifiers of the Tau protein."""
    df: pd.DataFrame = get_tau_modifiers(graph)
    return jsonify(df.to_json(index=False))


@app.route('/kinases.json')
def kinases_json():
    """Show the kinases in the graph."""
    df: pd.DataFrame = get_kinases(graph)
    return jsonify(df.to_json(index=False))


@app.route('/references.json')
def tau_references_json():
    """Show the modifiers of the Tau protein."""
    rows = get_tau_references(graph)
    return jsonify([
        dict(zip(('type', 'reference'), row))
        for row in rows
    ])


if __name__ == '__main__':
    app.run()
