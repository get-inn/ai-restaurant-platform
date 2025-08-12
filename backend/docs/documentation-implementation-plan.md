# Documentation Implementation Plan

## Quick Start (5-minute setup)

### Option 1: Immediate Usage Analysis

```bash
# Make the script executable
chmod +x scripts/analyze_code_usage.py

# Run comprehensive analysis
python scripts/analyze_code_usage.py --root src

# Analyze just bot management
python scripts/analyze_code_usage.py --module bot_manager

# Generate JSON report for tooling
python scripts/analyze_code_usage.py --output-format json --output-file docs/code-analysis.json
```

**Output Example**:
```
================================================================================
CODE USAGE ANALYSIS REPORT
================================================================================

CLASSES FOUND: 8
----------------------------------------

📋 Class: DialogManager
   File: bot_manager/dialog_manager.py:36
   Methods: 15
   Description: Main dialog management component for handling bot conversations.
     • __init__() - line 42
     • register_platform_adapter() - line 64
     • process_incoming_message() - line 77
     • handle_text_message() - line 215
     • send_message() - line 708
   📊 Total Usages: 23
     method_calls: 18 occurrences
       - api/routers/webhooks/telegram.py:45
       - api/services/bots/dialog_service.py:123
       - tests/test_dialog_manager.py:67
     ... and 15 more

⚠️  POTENTIALLY UNUSED CLASSES: 2
   - UnusedHelper
   - DeprecatedProcessor
```

### Option 2: Quick pdoc3 Documentation

```bash
# Install and generate docs in 5 minutes
pip install pdoc3

# Generate HTML documentation
pdoc --html --output-dir docs/generated --force src/bot_manager

# Serve locally
pdoc --http :8080 src/bot_manager
```

Open http://localhost:8080 to browse your documentation.

## Recommended Implementation Timeline

### Week 1: Foundation (2-3 hours)

**Day 1: Analysis & Planning**
- [ ] Run usage analysis script on entire codebase
- [ ] Review current docstring coverage
- [ ] Identify priority classes/modules for documentation

**Day 2: Quick Wins**
- [ ] Set up pdoc3 for immediate documentation
- [ ] Configure IDE with recommended extensions
- [ ] Create basic documentation workflow

### Week 2: Professional Setup (4-6 hours)

**Day 1: Sphinx Setup**
- [ ] Install and configure Sphinx
- [ ] Create documentation structure
- [ ] Set up automated builds

**Day 2: Integration**
- [ ] Integrate with CI/CD pipeline
- [ ] Set up GitHub Pages or internal hosting
- [ ] Configure team IDE settings

### Week 3: Enhancement (2-4 hours)

**Day 1: Advanced Features**
- [ ] Add cross-references and intersphinx
- [ ] Create usage examples and guides
- [ ] Set up documentation linting

**Day 2: Maintenance**
- [ ] Create documentation maintenance processes
- [ ] Train team on documentation tools
- [ ] Set up monitoring and alerts

## Detailed Implementation Steps

### Step 1: Immediate Analysis

```bash
# Create analysis directory
mkdir -p docs/analysis

# Run comprehensive analysis
python scripts/analyze_code_usage.py --output-file docs/analysis/code-usage-$(date +%Y%m%d).txt

# Generate JSON for tooling
python scripts/analyze_code_usage.py --output-format json --output-file docs/analysis/code-usage.json
```

### Step 2: Set Up pdoc3 (Quickest Option)

```bash
# Install pdoc3
echo "pdoc3==0.10.0" >> requirements-dev.txt
pip install -r requirements-dev.txt

# Create documentation script
cat > scripts/generate_quick_docs.sh << 'EOF'
#!/bin/bash
echo "🚀 Generating documentation..."

# Clean and create output directory
rm -rf docs/generated
mkdir -p docs/generated

# Generate documentation for bot management system
pdoc --html \
  --output-dir docs/generated \
  --config show_source_code=True \
  --config sort_identifiers=True \
  --config list_class_variables_in_index=True \
  --force \
  src/bot_manager \
  src/api/routers/bots \
  src/api/services/bots \
  src/api/models/bots.py

echo "✅ Documentation generated in docs/generated/"
echo "🌐 Run: python -m http.server 8080 --directory docs/generated"
EOF

chmod +x scripts/generate_quick_docs.sh

# Generate documentation
./scripts/generate_quick_docs.sh
```

### Step 3: Set Up Sphinx (Professional Option)

```bash
# Install Sphinx and extensions
cat >> requirements-dev.txt << 'EOF'
sphinx==7.2.6
sphinx-autodoc-typehints==1.24.0
sphinx-rtd-theme==1.3.0
myst-parser==2.0.0
sphinx-autobuild==2024.2.4
EOF

pip install -r requirements-dev.txt

# Initialize Sphinx
mkdir -p docs/sphinx
cd docs/sphinx
sphinx-quickstart --quiet --project "Bot Management System" --author "GetInn Team"

# Copy our pre-configured files
# (conf.py and index.rst files are provided in setup-sphinx-documentation.md)

# Build documentation
make html

# Set up auto-rebuild for development
sphinx-autobuild source build/html --host 0.0.0.0 --port 8080
```

### Step 4: CI/CD Integration

```yaml
# .github/workflows/documentation.yml
name: Documentation

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  docs:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout
      uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Install dependencies
      run: |
        pip install -r requirements-dev.txt
        
    - name: Generate usage analysis
      run: |
        python scripts/analyze_code_usage.py --output-file docs/analysis/usage-report.txt
        
    - name: Build Sphinx documentation
      run: |
        cd docs/sphinx && make html
        
    - name: Deploy to GitHub Pages
      if: github.ref == 'refs/heads/main'
      uses: peaceiris/actions-gh-pages@v3
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: docs/sphinx/build/html
```

### Step 5: Team Setup

```bash
# Create team setup script
cat > scripts/setup_dev_docs.sh << 'EOF'
#!/bin/bash
echo "🔧 Setting up documentation tools for development..."

# Install development dependencies
pip install -r requirements-dev.txt

# Configure git hooks for documentation
cat > .git/hooks/pre-commit << 'HOOK'
#!/bin/bash
# Check if documentation needs updating
if git diff --cached --name-only | grep -E "\.(py)$" > /dev/null; then
    echo "🔍 Python files changed, checking documentation..."
    python scripts/analyze_code_usage.py --output-file /tmp/usage-check.txt
    echo "📚 Consider updating documentation if new classes/methods were added"
fi
HOOK

chmod +x .git/hooks/pre-commit

echo "✅ Development documentation tools configured"
echo "📖 Run './scripts/generate_quick_docs.sh' to generate docs"
echo "🚀 Run 'sphinx-autobuild docs/sphinx/source docs/sphinx/build/html' for live preview"
EOF

chmod +x scripts/setup_dev_docs.sh
```

## Usage Examples

### Finding Class Usage

```bash
# Find all usages of DialogManager
python scripts/analyze_code_usage.py --module bot_manager | grep -A 10 "DialogManager"

# Get JSON output for programmatic use
python scripts/analyze_code_usage.py --output-format json | jq '.classes.DialogManager.usage'
```

### IDE Integration

**VSCode**:
1. Install Python extension
2. Install autodocstring extension  
3. Use Ctrl+Shift+P → "Python: Generate Docstring"
4. Use F12 for "Go to Definition"
5. Use Shift+F12 for "Find All References"

**PyCharm**:
1. Use Ctrl+Q for quick documentation
2. Use Ctrl+B for "Go to Declaration"
3. Use Alt+F7 for "Find Usages"
4. Use Ctrl+H for class hierarchy

### Automated Documentation Updates

```bash
# Add to your development workflow
cat >> .vscode/tasks.json << 'EOF'
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Update Documentation",
            "type": "shell",
            "command": "${workspaceFolder}/scripts/generate_quick_docs.sh",
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always"
            }
        },
        {
            "label": "Analyze Code Usage",
            "type": "shell", 
            "command": "python",
            "args": ["scripts/analyze_code_usage.py"],
            "group": "test"
        }
    ]
}
EOF
```

## Expected Results

### After Quick Setup (pdoc3)
- ✅ Complete API documentation with search
- ✅ Class/method cross-references
- ✅ Source code links
- ✅ Usage analysis report
- ⏱️ **Time**: 10-15 minutes

### After Professional Setup (Sphinx)
- ✅ Publication-quality documentation  
- ✅ Multiple output formats (HTML, PDF)
- ✅ Advanced cross-referencing
- ✅ Integration with external docs
- ✅ Automated CI/CD pipeline
- ⏱️ **Time**: 2-4 hours

### After Full Implementation
- ✅ Complete code visibility
- ✅ Usage tracking across codebase
- ✅ IDE integration for navigation
- ✅ Automated maintenance
- ✅ Team collaboration features
- ⏱️ **Time**: 1-2 weeks

## Maintenance Workflow

### Daily (Automated)
- [ ] CI/CD builds documentation on code changes
- [ ] Usage analysis runs on pull requests
- [ ] Documentation links validated

### Weekly (5 minutes)
- [ ] Review usage analysis for new classes
- [ ] Check for undocumented methods
- [ ] Update examples if needed

### Monthly (30 minutes)
- [ ] Review documentation coverage
- [ ] Update team IDE configurations
- [ ] Clean up unused code identified by analysis

## Troubleshooting

### Common Issues

**"Module not found" errors**:
```bash
# Ensure PYTHONPATH includes src directory
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"
python scripts/analyze_code_usage.py
```

**Missing dependencies**:
```bash
# Install all development dependencies
pip install -r requirements-dev.txt
```

**Sphinx build errors**:
```bash
# Clean and rebuild
cd docs/sphinx
make clean
make html
```

**Empty usage analysis**:
```bash
# Ensure you're analyzing the right directory
python scripts/analyze_code_usage.py --root src --module bot_manager
```

## Next Steps

1. **Choose your approach**: Start with pdoc3 for immediate results, migrate to Sphinx for professional needs
2. **Run the analysis**: Use the usage analysis script to understand your current codebase
3. **Set up IDE integration**: Configure your development environment for better navigation
4. **Establish workflow**: Integrate documentation generation into your development process
5. **Train your team**: Share the tools and processes with your development team

The combination of these tools will give you comprehensive visibility into your codebase structure, usage patterns, and provide professional documentation for your bot management system.