# IDE Integration Guide for Code Documentation

## Visual Studio Code Setup

### Essential Extensions

```bash
# Install recommended extensions
code --install-extension ms-python.python
code --install-extension ms-python.pylint  
code --install-extension ms-python.mypy-type-checker
code --install-extension njpwerner.autodocstring
code --install-extension kosz78.nim-docstring-generator
code --install-extension wholroyd.jinja
```

### VSCode Settings Configuration

```json
// .vscode/settings.json
{
    "python.analysis.typeCheckingMode": "strict",
    "python.analysis.autoImportCompletions": true,
    "python.analysis.includePackageSymbolsInAutoImport": true,
    "python.analysis.autoSearchPaths": true,
    "python.analysis.diagnosticMode": "workspace",
    "python.defaultInterpreterPath": "./venv/bin/python",
    
    // Documentation
    "autoDocstring.docstringFormat": "google",
    "autoDocstring.startOnNewLine": false,
    "autoDocstring.includeExtendedSummary": true,
    "autoDocstring.includeName": false,
    
    // Pylint configuration
    "pylint.args": [
        "--load-plugins=pylint_django",
        "--django-settings-module=settings"
    ],
    
    // MyPy configuration  
    "mypy-type-checker.args": [
        "--ignore-missing-imports",
        "--show-error-codes"
    ]
}
```

### Workspace Configuration

```json
// .vscode/tasks.json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Generate Documentation",
            "type": "shell",
            "command": "python",
            "args": ["scripts/analyze_code_usage.py"],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            }
        },
        {
            "label": "Build Sphinx Docs",
            "type": "shell",
            "command": "make",
            "args": ["docs"],
            "group": "build",
            "options": {
                "cwd": "${workspaceFolder}"
            }
        }
    ]
}
```

## PyCharm Setup

### Enable Advanced Features

1. **Go to Settings → Tools → Python Integrated Tools**
   - Docstring format: Google
   - Render external documentation: Enabled

2. **Code → Generate → Documentation String**
   - Automatically generates docstrings for functions/classes

3. **View → Tool Windows → Structure**
   - Shows all classes/methods in current file

4. **Navigate → Go to Declaration/Usages**
   - Find where classes/methods are used (Ctrl+B, Alt+F7)

### Custom File Templates

```python
# File and Code Templates → Python Script
#!/usr/bin/env python3
"""
${NAME}

Brief description of the module.

Classes:
    ${CLASS_NAME}: Brief description

Functions:
    ${FUNCTION_NAME}: Brief description
"""

from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ${CLASS_NAME}:
    """Brief class description.
    
    Longer class description that can span multiple lines.
    
    Attributes:
        attribute_name: Description of attribute.
        
    Example:
        Basic usage example::
        
            instance = ${CLASS_NAME}()
            result = instance.method()
    """
    
    def __init__(self):
        """Initialize the class."""
        pass
        
    def method_name(self, param: str) -> str:
        """Brief method description.
        
        Args:
            param: Description of parameter.
            
        Returns:
            Description of return value.
            
        Raises:
            ValueError: If param is invalid.
        """
        return param
```

## Neovim/Vim Setup

### Language Server Protocol (LSP)

```lua
-- init.lua or init.vim equivalent
require('lspconfig').pylsp.setup{
    settings = {
        pylsp = {
            plugins = {
                pycodestyle = {enabled = false},
                pyflakes = {enabled = false},
                pylint = {enabled = true},
                rope_completion = {enabled = true},
                jedi_completion = {enabled = true, include_params = true},
                jedi_hover = {enabled = true},
                jedi_references = {enabled = true},
                jedi_signature_help = {enabled = true},
                jedi_symbols = {enabled = true, all_scopes = true},
            }
        }
    }
}
```

### Key Mappings for Navigation

```lua
-- Telescope for code navigation
vim.keymap.set('n', '<leader>ff', '<cmd>Telescope find_files<cr>')
vim.keymap.set('n', '<leader>fg', '<cmd>Telescope live_grep<cr>')
vim.keymap.set('n', '<leader>fs', '<cmd>Telescope lsp_document_symbols<cr>')
vim.keymap.set('n', '<leader>fr', '<cmd>Telescope lsp_references<cr>')

-- LSP mappings
vim.keymap.set('n', 'gd', vim.lsp.buf.definition)
vim.keymap.set('n', 'gr', vim.lsp.buf.references)  
vim.keymap.set('n', 'K', vim.lsp.buf.hover)
vim.keymap.set('n', '<leader>rn', vim.lsp.buf.rename)
```

## Command Line Tools

### ripgrep for Usage Search

```bash
# Install ripgrep
brew install ripgrep  # macOS
apt install ripgrep   # Ubuntu

# Find all usages of DialogManager class
rg "DialogManager" --type py src/

# Find method calls
rg "\.process_incoming_message\(" --type py src/

# Find imports
rg "from.*DialogManager" --type py src/
```

### fd for File Navigation

```bash
# Install fd
brew install fd  # macOS
apt install fd-find  # Ubuntu

# Find all Python files in bot_manager
fd -e py . src/bot_manager/

# Find files containing "dialog" in name
fd dialog src/
```

## Browser-based Navigation

### GitHub/GitLab Integration

```yaml
# .github/workflows/docs.yml
name: Generate Documentation

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Install dependencies
      run: |
        pip install -r requirements-dev.txt
        pip install sphinx sphinx-rtd-theme
        
    - name: Generate documentation
      run: |
        cd docs/sphinx && make html
        
    - name: Deploy to GitHub Pages
      uses: peaceiris/actions-gh-pages@v3
      if: github.ref == 'refs/heads/main'
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: ./docs/sphinx/build/html
```

## Advanced Analysis Tools

### Sourcegraph Integration

```bash
# Install Sourcegraph CLI
curl -L https://sourcegraph.com/.api/src-cli/src_linux_amd64 -o /usr/local/bin/src
chmod +x /usr/local/bin/src

# Search across codebase
src search "DialogManager" -repo="your-repo"
src search "def process_incoming_message" -repo="your-repo"
```

### Language Server Features

Most modern editors support these LSP features:

1. **Go to Definition** (F12)
2. **Find All References** (Shift+F12)
3. **Symbol Search** (Ctrl+T)
4. **Hover Information** (mouse over)
5. **Signature Help** (parameter hints)
6. **Code Completion**
7. **Refactoring Support**

### Tree-sitter for Syntax Highlighting

```lua
-- For Neovim with tree-sitter
require'nvim-treesitter.configs'.setup {
  ensure_installed = {"python", "json", "yaml", "markdown"},
  highlight = {
    enable = true,
  },
  incremental_selection = {
    enable = true,
  },
  textobjects = {
    select = {
      enable = true,
      keymaps = {
        ["af"] = "@function.outer",
        ["if"] = "@function.inner",
        ["ac"] = "@class.outer",
        ["ic"] = "@class.inner",
      },
    },
  },
}
```