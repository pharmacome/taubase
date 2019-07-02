# -*- coding: utf-8 -*-

"""Run TauBase."""

import logging

import click


@click.group()
def main():
    """TauBase."""


@main.command()
@click.option('-v', '--verbose', is_flag=True)
def web(verbose: bool):
    """Run the TauBase web application."""
    if verbose:
        logging.basicConfig(level=logging.INFO)
        logging.getLogger('pybel').setLevel(logging.INFO)
        logging.getLogger('hbp').setLevel(logging.INFO)

    from taubase.wsgi import app
    app.run()


if __name__ == '__main__':
    main()
