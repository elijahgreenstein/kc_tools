# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Kobe Collection Tools'
copyright = '2025, Elijah Greenstein'
author = 'Elijah Greenstein'
release = '0.1'

# -- Importing modules -------------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html
#
# autodoc analyses the code and docstrings by introspection after importing the
# modules. For importing to work, you have to make sure that your modules can be
# found by Sphinx and that dependencies can be resolved (if your module does
# import foo, but foo is not available in the python environment that Sphinx
# runs in, your module import will fail).
#
# It is alternatively possible to patch the Sphinx run so that it can operate
# directly on the sources; e.g. if you want to be able to do a Sphinx build from
# a source checkout.

import pathlib
import sys
sys.path.insert(0, str(pathlib.Path('..', '..', 'src').resolve()))

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
        "sphinx.ext.autosummary"
]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'classic'
html_static_path = ['_static']
