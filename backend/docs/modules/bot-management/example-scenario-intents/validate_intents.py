#!/usr/bin/env python3
"""
Intent Package Validation Script
--------------------------------
Validates the intent-based scenario package for correctness.

Usage:
    python validate_intents.py
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Set

def validate_intent_package():
    """Validate the entire intent package."""
    
    base_dir = Path(__file__).parent
    errors = []
    warnings = []
    
    # Load package.json
    package_file = base_dir / "package.json"
    if not package_file.exists():
        errors.append("package.json not found")
        return errors, warnings
    
    with open(package_file, 'r', encoding='utf-8') as f:
        package_data = json.load(f)
    
    # Collect all intent files
    intent_files = {}
    intents_data = {}
    
    for intent_type in ["core", "information", "support", "navigation"]:
        type_dir = base_dir / intent_type
        if type_dir.exists():
            for intent_file in type_dir.glob("*.json"):
                try:
                    with open(intent_file, 'r', encoding='utf-8') as f:
                        intent_data = json.load(f)
                        intent_id = intent_data.get("intent_id")
                        if intent_id:
                            intent_files[intent_id] = intent_file
                            intents_data[intent_id] = intent_data
                        else:
                            errors.append(f"No intent_id in {intent_file}")
                except json.JSONDecodeError as e:
                    errors.append(f"JSON error in {intent_file}: {e}")
                except Exception as e:
                    errors.append(f"Error loading {intent_file}: {e}")
    
    # Validate package deployment order
    deployment_order = package_data.get("deployment_order", [])
    expected_intents = set()
    
    for file_path in deployment_order:
        # Extract intent_id from file path
        intent_filename = file_path.split('/')[-1]
        # Find corresponding intent_id
        for intent_id, data in intents_data.items():
            if intent_filename.replace('_intent.json', '') in intent_id or intent_id in intent_filename:
                expected_intents.add(intent_id)
                break
    
    # Check all intents are in deployment order
    for intent_id in intents_data.keys():
        if intent_id not in expected_intents:
            warnings.append(f"Intent {intent_id} not in deployment_order")
    
    # Validate intent dependencies
    all_intent_ids = set(intents_data.keys())
    
    for intent_id, intent_data in intents_data.items():
        dependencies = intent_data.get("dependencies", [])
        for dep in dependencies:
            if dep not in all_intent_ids:
                errors.append(f"Intent {intent_id} depends on missing intent: {dep}")
    
    # Validate intent transitions
    for intent_id, intent_data in intents_data.items():
        steps = intent_data.get("steps", {})
        
        for step_id, step_data in steps.items():
            next_step = step_data.get("next_step")
            
            if isinstance(next_step, str) and next_step.startswith("intent://"):
                # Parse intent reference
                parts = next_step.replace("intent://", "").split("/")
                if len(parts) >= 2:
                    target_intent_type = parts[0]
                    target_intent_id = parts[1]
                    target_step = parts[2] if len(parts) > 2 else None
                    
                    # Check if target intent exists
                    if target_intent_id not in all_intent_ids:
                        errors.append(f"Step {step_id} in {intent_id} references missing intent: {target_intent_id}")
                    elif target_step:
                        # Check if target step exists
                        target_intent_data = intents_data[target_intent_id]
                        target_steps = target_intent_data.get("steps", {})
                        if target_step not in target_steps:
                            errors.append(f"Step {step_id} in {intent_id} references missing step {target_step} in {target_intent_id}")
            
            elif isinstance(next_step, dict) and next_step.get("type") == "conditional":
                # Validate conditional transitions
                conditions = next_step.get("conditions", [])
                for condition in conditions:
                    then_step = condition.get("then")
                    if isinstance(then_step, str) and then_step.startswith("intent://"):
                        # Same validation as above
                        parts = then_step.replace("intent://", "").split("/")
                        if len(parts) >= 2:
                            target_intent_id = parts[1]
                            if target_intent_id not in all_intent_ids:
                                errors.append(f"Conditional in step {step_id} of {intent_id} references missing intent: {target_intent_id}")
    
    # Validate required fields in each intent
    required_fields = ["intent_id", "intent_name", "intent_type", "version", "start_step", "steps"]
    
    for intent_id, intent_data in intents_data.items():
        for field in required_fields:
            if field not in intent_data:
                errors.append(f"Intent {intent_id} missing required field: {field}")
        
        # Check start_step exists
        start_step = intent_data.get("start_step")
        steps = intent_data.get("steps", {})
        if start_step and start_step not in steps:
            errors.append(f"Intent {intent_id} start_step '{start_step}' not found in steps")
    
    return errors, warnings

def main():
    """Main validation function."""
    print("🔍 Validating ChiHo Intent Package...")
    print("=" * 50)
    
    errors, warnings = validate_intent_package()
    
    if warnings:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"   • {warning}")
        print()
    
    if errors:
        print("❌ ERRORS:")
        for error in errors:
            print(f"   • {error}")
        print()
        print(f"❌ Validation failed with {len(errors)} error(s)")
        return 1
    else:
        print("✅ All validations passed!")
        print()
        
        # Print package summary
        base_dir = Path(__file__).parent
        intent_count = len(list(base_dir.glob("*/*.json")))
        
        package_file = base_dir / "package.json"
        with open(package_file, 'r', encoding='utf-8') as f:
            package_data = json.load(f)
        
        print("📊 Package Summary:")
        print(f"   • Package: {package_data.get('package_name')}")
        print(f"   • Version: {package_data.get('version')}")
        print(f"   • Intents: {intent_count}")
        print(f"   • Categories: {len(package_data.get('activation_groups', {}))}")
        
        return 0

if __name__ == "__main__":
    exit(main())