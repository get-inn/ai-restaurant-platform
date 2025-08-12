#!/usr/bin/env python3
"""
Code Usage Analyzer

This script analyzes the codebase to find:
1. All classes and their methods
2. Where each class/method is imported and used
3. Generate a comprehensive usage report

Usage:
    python scripts/analyze_code_usage.py
    python scripts/analyze_code_usage.py --output-format json
    python scripts/analyze_code_usage.py --module bot_manager
"""

import ast
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from collections import defaultdict
import re

class CodeAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze Python code structure and usage."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.classes = {}
        self.functions = {}
        self.imports = {}
        self.class_methods = defaultdict(list)
        self.current_class = None
        self.usages = defaultdict(list)
        
    def visit_ClassDef(self, node):
        """Visit class definitions."""
        self.current_class = node.name
        class_info = {
            'name': node.name,
            'line': node.lineno,
            'docstring': ast.get_docstring(node) or '',
            'methods': [],
            'bases': [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases],
            'file': self.file_path
        }
        self.classes[node.name] = class_info
        
        # Visit methods within this class
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = {
                    'name': item.name,
                    'line': item.lineno,
                    'docstring': ast.get_docstring(item) or '',
                    'args': [arg.arg for arg in item.args.args],
                    'class': node.name,
                    'file': self.file_path
                }
                class_info['methods'].append(method_info)
                self.class_methods[node.name].append(item.name)
        
        self.generic_visit(node)
        self.current_class = None
    
    def visit_FunctionDef(self, node):
        """Visit function definitions (not in classes)."""
        if self.current_class is None:  # Only top-level functions
            func_info = {
                'name': node.name,
                'line': node.lineno,
                'docstring': ast.get_docstring(node) or '',
                'args': [arg.arg for arg in node.args.args],
                'file': self.file_path
            }
            self.functions[node.name] = func_info
        
        self.generic_visit(node)
    
    def visit_Import(self, node):
        """Visit import statements."""
        for alias in node.names:
            self.imports[alias.name] = {
                'type': 'import',
                'module': alias.name,
                'alias': alias.asname,
                'line': node.lineno,
                'file': self.file_path
            }
    
    def visit_ImportFrom(self, node):
        """Visit from...import statements."""
        module = node.module or ''
        for alias in node.names:
            import_key = f"{module}.{alias.name}" if module else alias.name
            self.imports[import_key] = {
                'type': 'from_import',
                'module': module,
                'name': alias.name,
                'alias': alias.asname,
                'line': node.lineno,
                'file': self.file_path
            }
    
    def visit_Call(self, node):
        """Visit function/method calls to track usage."""
        if isinstance(node.func, ast.Name):
            # Direct function call
            self.usages[node.func.id].append({
                'type': 'function_call',
                'line': node.lineno,
                'file': self.file_path
            })
        elif isinstance(node.func, ast.Attribute):
            # Method call (obj.method())
            if isinstance(node.func.value, ast.Name):
                usage_key = f"{node.func.value.id}.{node.func.attr}"
                self.usages[usage_key].append({
                    'type': 'method_call',
                    'object': node.func.value.id,
                    'method': node.func.attr,
                    'line': node.lineno,
                    'file': self.file_path
                })
        
        self.generic_visit(node)
    
    def visit_Name(self, node):
        """Visit name references (variable access)."""
        if isinstance(node.ctx, ast.Load):  # Only when loading/reading the name
            self.usages[node.id].append({
                'type': 'name_reference',
                'line': node.lineno,
                'file': self.file_path
            })
        
        self.generic_visit(node)


class UsageTracker:
    """Track usage of classes and methods across the codebase."""
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.analyzers = {}
        self.global_classes = {}
        self.global_functions = {}
        self.usage_map = defaultdict(list)
        
    def analyze_file(self, file_path: Path) -> Optional[CodeAnalyzer]:
        """Analyze a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            analyzer = CodeAnalyzer(str(file_path.relative_to(self.root_path)))
            analyzer.visit(tree)
            
            return analyzer
        except (SyntaxError, UnicodeDecodeError) as e:
            print(f"Error analyzing {file_path}: {e}")
            return None
    
    def analyze_directory(self, directory: Path, pattern: str = "**/*.py"):
        """Analyze all Python files in a directory."""
        print(f"Analyzing directory: {directory}")
        
        for file_path in directory.glob(pattern):
            if file_path.is_file() and not file_path.name.startswith('.'):
                analyzer = self.analyze_file(file_path)
                if analyzer:
                    self.analyzers[str(file_path.relative_to(self.root_path))] = analyzer
                    
                    # Merge into global collections
                    self.global_classes.update(analyzer.classes)
                    self.global_functions.update(analyzer.functions)
                    
                    # Merge usage information
                    for usage_key, usages in analyzer.usages.items():
                        self.usage_map[usage_key].extend(usages)
    
    def find_class_usage(self, class_name: str) -> Dict[str, List[Dict]]:
        """Find all usages of a specific class."""
        usages = defaultdict(list)
        
        # Direct class references
        if class_name in self.usage_map:
            usages['direct_references'] = self.usage_map[class_name]
        
        # Method calls on class instances
        for usage_key, usage_list in self.usage_map.items():
            if '.' in usage_key:
                obj, method = usage_key.split('.', 1)
                # This is a simplified heuristic - in practice, you'd need more sophisticated analysis
                if obj.lower() == class_name.lower() or method in self.get_class_methods(class_name):
                    usages['method_calls'].extend(usage_list)
        
        # Import statements
        for analyzer in self.analyzers.values():
            for import_key, import_info in analyzer.imports.items():
                if class_name in import_key:
                    usages['imports'].append(import_info)
        
        return dict(usages)
    
    def get_class_methods(self, class_name: str) -> List[str]:
        """Get all methods for a class."""
        if class_name in self.global_classes:
            return [method['name'] for method in self.global_classes[class_name]['methods']]
        return []
    
    def generate_report(self, output_format: str = 'text') -> str:
        """Generate a comprehensive usage report."""
        if output_format == 'json':
            return self._generate_json_report()
        else:
            return self._generate_text_report()
    
    def _generate_text_report(self) -> str:
        """Generate a human-readable text report."""
        report = []
        report.append("=" * 80)
        report.append("CODE USAGE ANALYSIS REPORT")
        report.append("=" * 80)
        report.append()
        
        # Classes summary
        report.append(f"CLASSES FOUND: {len(self.global_classes)}")
        report.append("-" * 40)
        
        for class_name, class_info in sorted(self.global_classes.items()):
            report.append(f"\n📋 Class: {class_name}")
            report.append(f"   File: {class_info['file']}:{class_info['line']}")
            report.append(f"   Methods: {len(class_info['methods'])}")
            
            if class_info['docstring']:
                # First line of docstring
                first_line = class_info['docstring'].split('\n')[0]
                report.append(f"   Description: {first_line}")
            
            # Show methods
            for method in class_info['methods'][:5]:  # Show first 5 methods
                report.append(f"     • {method['name']}() - line {method['line']}")
            
            if len(class_info['methods']) > 5:
                report.append(f"     ... and {len(class_info['methods']) - 5} more methods")
            
            # Show usage
            usage = self.find_class_usage(class_name)
            total_usages = sum(len(usage_list) for usage_list in usage.values())
            
            if total_usages > 0:
                report.append(f"   📊 Total Usages: {total_usages}")
                
                # Show some usage examples
                for usage_type, usage_list in usage.items():
                    if usage_list and usage_type != 'imports':
                        report.append(f"     {usage_type}: {len(usage_list)} occurrences")
                        for usage in usage_list[:3]:  # Show first 3 examples
                            report.append(f"       - {usage['file']}:{usage['line']}")
                        if len(usage_list) > 3:
                            report.append(f"       ... and {len(usage_list) - 3} more")
            else:
                report.append("   ⚠️  No usages found (might be unused)")
        
        # Functions summary
        report.append(f"\n\nFUNCTIONS FOUND: {len(self.global_functions)}")
        report.append("-" * 40)
        
        for func_name, func_info in sorted(self.global_functions.items()):
            report.append(f"\n🔧 Function: {func_name}")
            report.append(f"   File: {func_info['file']}:{func_info['line']}")
            
            if func_info['docstring']:
                first_line = func_info['docstring'].split('\n')[0]
                report.append(f"   Description: {first_line}")
            
            # Show usage
            if func_name in self.usage_map:
                usages = self.usage_map[func_name]
                report.append(f"   📊 Usages: {len(usages)}")
                for usage in usages[:3]:
                    report.append(f"     - {usage['file']}:{usage['line']}")
                if len(usages) > 3:
                    report.append(f"     ... and {len(usages) - 3} more")
            else:
                report.append("   ⚠️  No usages found")
        
        # Summary statistics
        report.append(f"\n\nSUMMARY STATISTICS")
        report.append("-" * 40)
        report.append(f"Total files analyzed: {len(self.analyzers)}")
        report.append(f"Total classes: {len(self.global_classes)}")
        report.append(f"Total functions: {len(self.global_functions)}")
        report.append(f"Total methods: {sum(len(cls['methods']) for cls in self.global_classes.values())}")
        
        # Potentially unused classes
        unused_classes = []
        for class_name in self.global_classes:
            usage = self.find_class_usage(class_name)
            total_usages = sum(len(usage_list) for usage_list in usage.values())
            if total_usages == 0:
                unused_classes.append(class_name)
        
        if unused_classes:
            report.append(f"\n⚠️  POTENTIALLY UNUSED CLASSES: {len(unused_classes)}")
            for class_name in unused_classes:
                report.append(f"   - {class_name}")
        
        return '\n'.join(report)
    
    def _generate_json_report(self) -> str:
        """Generate a JSON report for programmatic use."""
        report_data = {
            'summary': {
                'files_analyzed': len(self.analyzers),
                'classes_found': len(self.global_classes),
                'functions_found': len(self.global_functions),
                'total_methods': sum(len(cls['methods']) for cls in self.global_classes.values())
            },
            'classes': {},
            'functions': self.global_functions,
            'usage_map': dict(self.usage_map)
        }
        
        # Add usage information to classes
        for class_name, class_info in self.global_classes.items():
            usage = self.find_class_usage(class_name)
            report_data['classes'][class_name] = {
                **class_info,
                'usage': usage,
                'total_usages': sum(len(usage_list) for usage_list in usage.values())
            }
        
        return json.dumps(report_data, indent=2, default=str)


def main():
    parser = argparse.ArgumentParser(description='Analyze code usage in the bot management system')
    parser.add_argument('--root', default='src', help='Root directory to analyze')
    parser.add_argument('--module', help='Specific module to analyze (e.g., bot_manager)')
    parser.add_argument('--output-format', choices=['text', 'json'], default='text', 
                       help='Output format')
    parser.add_argument('--output-file', help='Output file (default: stdout)')
    
    args = parser.parse_args()
    
    root_path = Path(args.root)
    if not root_path.exists():
        print(f"Error: Root path {root_path} does not exist")
        sys.exit(1)
    
    tracker = UsageTracker(root_path)
    
    if args.module:
        # Analyze specific module
        module_path = root_path / args.module
        if module_path.exists():
            tracker.analyze_directory(module_path)
        else:
            print(f"Error: Module path {module_path} does not exist")
            sys.exit(1)
    else:
        # Analyze all Python files
        tracker.analyze_directory(root_path)
    
    # Generate report
    report = tracker.generate_report(args.output_format)
    
    if args.output_file:
        with open(args.output_file, 'w') as f:
            f.write(report)
        print(f"Report generated: {args.output_file}")
    else:
        print(report)


if __name__ == '__main__':
    main()