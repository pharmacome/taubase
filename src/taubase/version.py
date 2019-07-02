# -*- coding: utf-8 -*-

"""Version information for TauBase."""

__all__ = [
    'VERSION',
    'get_version'
]

VERSION = '0.0.1-dev'


def get_version() -> str:
    """Get the software version of TauBase."""
    return VERSION
