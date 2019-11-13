# -*- coding: utf-8 -*-

"""Run TauBase."""

import logging
import sys
from collections import Counter

import click
from pybel.struct.summary import iterate_pubmed_identifiers

from .repository import repository


@click.group()
def main():
    """TauBase."""


@main.command()
@click.option('-d', '--directory', type=click.Path(dir_okay=True, file_okay=False, exists=True))
@click.option('-c', '--no-use-cached', is_flag=True)
def export(directory: str, no_use_cached: bool):
    """Export the repository."""
    repository.get_graph(
        directory=directory,
        use_cached=(directory or not no_use_cached),
    )


@main.command()
@click.option('-d', '--directory', type=click.Path(dir_okay=True, file_okay=False, exists=True))
@click.option('-c', '--no-use-cached', is_flag=True)
@click.option('-o', '--output', type=click.File('w'), default=sys.stdout)
def citations(directory: str, no_use_cached: bool, output):
    """Export the repository."""
    graph = repository.get_graph(
        directory=directory,
        use_cached=(directory or not no_use_cached),
    )

    c = Counter(iterate_pubmed_identifiers(graph))

    print('Citation', 'Count', sep='\t', file=output)
    for pmid, count in c.most_common():
        try:
            pmid = int(pmid)
        except ValueError:
            continue
        print(pmid, count, file=output, sep='\t')


@main.command()
@click.option('--host', type=str, default='0.0.0.0', help='Flask host.', show_default=True)
@click.option('--port', type=int, default=5000, help='Flask port.', show_default=True)
@click.option('-v', '--verbose', is_flag=True)
def web(host: str, port: int, verbose: bool):
    """Run the TauBase web application."""
    if verbose:
        logging.basicConfig(level=logging.INFO)
        logging.getLogger('pybel').setLevel(logging.INFO)
        logging.getLogger('hbp').setLevel(logging.INFO)

    from .wsgi import app
    app.run(host=host, port=port)


if __name__ == '__main__':
    main()
