#!/bin/bash
# Build GET INN Restaurant Platform Documentation

set -e

echo "🚀 Building GET INN Restaurant Platform Documentation..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements-docs.txt"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Change to Sphinx directory
cd docs

# Clean previous builds
echo "🧹 Cleaning previous builds..."
make clean

# Build HTML documentation
echo "📚 Building HTML documentation..."
make html

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "✅ Documentation built successfully!"
    echo "📖 Documentation location: $(pwd)/build/html/"
    echo "📄 Main file: $(pwd)/build/html/index.html"
    echo ""
    echo "🌐 To serve locally:"
    echo "   cd $(pwd)/build/html && python -m http.server 8080"
    echo "   Then open http://localhost:8080"
    echo ""
    echo "📋 Available pages:"
    echo "   • Main Documentation: index.html"
    echo "   • API Reference: api/index.html" 
    echo "   • Bot Management API: api/bot-management.html"
else
    echo "❌ Documentation build failed!"
    exit 1
fi