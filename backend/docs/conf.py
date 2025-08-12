# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Add both the backend and src directories to the Python path
backend_dir = os.path.abspath('../')
src_dir = os.path.abspath('../src')
sys.path.insert(0, backend_dir)
sys.path.insert(0, src_dir)

# Print paths for debugging
print(f"Backend directory: {backend_dir}")
print(f"Source directory: {src_dir}")
print(f"Python path: {sys.path[:3]}")

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'GET INN Restaurant Platform'
copyright = '2025, GetInn Team'
author = 'GetInn Team'
release = '1.0'
version = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'myst_parser',  # Enable MyST markdown parser
    'sphinx_design',  # Grid layouts and design elements
    'sphinxcontrib.mermaid',  # Mermaid diagrams
    'sphinx_tabs.tabs',  # Tabbed content
]

templates_path = ['_templates']
exclude_patterns = [
    'README.md',
    'documentation-implementation-plan.md', 
    'ide-integration-guide.md',
    'integrations/bot-labor-onboarding.md',
    '_build',
    'Thumbs.db',
    '.DS_Store',
]

language = 'en'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = []

# Theme options
html_theme_options = {}

html_title = "GET INN Restaurant Platform Documentation"
html_short_title = "GET INN Platform"

# -- Extension configuration -------------------------------------------------

# Autodoc configuration
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# Mock external dependencies that might not be available during doc build
autodoc_mock_imports = [
    'sqlalchemy',
    'fastapi',
    'pydantic',
    'celery',
    'redis',
    'psycopg2',
    'alembic',
    'bcrypt',
    'jwt',
    'telegram',
    'azure',
    'openai',
    'uvicorn'
]

# Suppress warnings about missing modules
suppress_warnings = ['autodoc.import_object']

# Napoleon settings for Google/NumPy style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True

# Autosummary settings (disabled for now)
# autosummary_generate = True
# autosummary_imported_members = True

# Todo extension configuration
todo_include_todos = True

# Intersphinx mapping for external documentation (simplified)
# intersphinx_mapping = {
#     'python': ('https://docs.python.org/3/', None),
# }

# Type hints configuration
typehints_fully_qualified = False
always_document_param_types = True
typehints_document_rtype = True

# MyST configuration for relative paths
myst_url_schemes = ["http", "https", "mailto"]

# Copy button configuration
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True
copybutton_only_copy_prompt_lines = True

# Mermaid configuration
mermaid_output_format = 'raw'
mermaid_init_js = "mermaid.initialize({startOnLoad:true});"

# Source file suffixes - support both RST and Markdown
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# MyST parser configuration for Markdown support
myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
    "attrs_inline",
    "attrs_block",
]