# -*- coding: utf-8 -*-

"""Run TauBase."""

import logging

import click


@click.group()
def main():
    """TauBase."""


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
