#!/usr/bin/env python
"""
Verification script to test the independence of the Flask project.
"""
import os
import sys
import ast
import importlib.util
from pathlib import Path

def find_python_files(directory):
    """Find all Python files in the directory."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip venv and __pycache__ directories
        dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', 'migrations']]
        
        for file in files:
            if file.endswith('.py') and file not in ['verify_independence.py', 'setup.py']:
                python_files.append(os.path.join(root, file))
    
    return python_files

def check_imports(file_path):
    """Check for imports that might reference parent directories."""
    external_imports = []
    problematic_imports = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the AST
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name
                        if module_name.startswith('..'):
                            problematic_imports.append(f"import {module_name}")
                        elif not module_name.startswith(('app', 'processing', 'config')):
                            external_imports.append(f"import {module_name}")
                
                elif isinstance(node, ast.ImportFrom):
                    module_name = node.module or ''
                    if module_name.startswith('..'):
                        problematic_imports.append(f"from {module_name} import ...")
                    elif module_name and not module_name.startswith(('app', 'processing', 'config')):
                        # Check if it's a built-in or external library
                        if '.' not in module_name or module_name.split('.')[0] not in [
                            'os', 'sys', 'datetime', 'decimal', 'json', 'csv', 'io', 're'
                        ]:
                            external_imports.append(f"from {module_name} import ...")
    
    except Exception as e:
        print(f"⚠️  Error parsing {file_path}: {e}")
        return [], []
    
    return external_imports, problematic_imports

def check_file_references(file_path):
    """Check for hardcoded file paths that might reference parent directories."""
    problematic_paths = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for potential path references
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if '../' in line and not line.strip().startswith('#'):
                problematic_paths.append(f"Line {i}: {line.strip()}")
    
    except Exception as e:
        print(f"⚠️  Error reading {file_path}: {e}")
    
    return problematic_paths

def check_project_structure():
    """Check if all required directories and files exist."""
    required_items = [
        'app',
        'app/__init__.py',
        'app/models.py',
        'app/auth',
        'app/transcripts',
        'app/corrections',
        'app/wordlists',
        'app/api',
        'processing',
        'processing/__init__.py',
        'processing/openai_service.py',
        'processing/csv_parser.py',
        'templates',
        'static',
        'config.py',
        'requirements.txt',
        'app.py',
        '.env.example'
    ]
    
    missing_items = []
    for item in required_items:
        if not os.path.exists(item):
            missing_items.append(item)
    
    return missing_items

def verify_requirements():
    """Check if requirements.txt contains all necessary dependencies."""
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read().lower()
        
        required_packages = [
            'flask',
            'flask-sqlalchemy',
            'flask-migrate',
            'flask-login',
            'flask-wtf',
            'pymysql',
            'openai',
            'werkzeug'
        ]
        
        missing_packages = []
        for package in required_packages:
            if package not in requirements:
                missing_packages.append(package)
        
        return missing_packages
    
    except FileNotFoundError:
        return ['requirements.txt not found']

def main():
    """Main verification function."""
    print("🔍 Flask Project Independence Verification")
    print("=" * 50)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Check project structure
    print("\n📁 Checking project structure...")
    missing_items = check_project_structure()
    if missing_items:
        print("❌ Missing required items:")
        for item in missing_items:
            print(f"   - {item}")
    else:
        print("✅ All required files and directories present")
    
    # Check requirements
    print("\n📦 Checking requirements.txt...")
    missing_packages = verify_requirements()
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
    else:
        print("✅ All required packages listed in requirements.txt")
    
    # Check Python files for imports
    print("\n🐍 Checking Python files for problematic imports...")
    python_files = find_python_files('.')
    
    total_problematic = 0
    all_external_imports = set()
    
    for file_path in python_files:
        external_imports, problematic_imports = check_imports(file_path)
        file_paths = check_file_references(file_path)
        
        all_external_imports.update(external_imports)
        
        if problematic_imports or file_paths:
            total_problematic += 1
            print(f"\n⚠️  Issues in {file_path}:")
            
            if problematic_imports:
                print("   Problematic imports:")
                for imp in problematic_imports:
                    print(f"     - {imp}")
            
            if file_paths:
                print("   Problematic file paths:")
                for path in file_paths:
                    print(f"     - {path}")
    
    if total_problematic == 0:
        print("✅ No problematic imports or file references found")
    else:
        print(f"\n❌ Found issues in {total_problematic} files")
    
    # Show external dependencies (informational)
    if all_external_imports:
        print(f"\n📋 External dependencies found:")
        for imp in sorted(all_external_imports):
            print(f"   - {imp}")
    
    # Final assessment
    print("\n🎯 Independence Assessment:")
    independence_score = 0
    max_score = 4
    
    if not missing_items:
        independence_score += 1
        print("✅ Project structure: Complete")
    else:
        print("❌ Project structure: Incomplete")
    
    if not missing_packages:
        independence_score += 1
        print("✅ Dependencies: All listed")
    else:
        print("❌ Dependencies: Missing packages")
    
    if total_problematic == 0:
        independence_score += 2
        print("✅ Import independence: Verified")
    else:
        print("❌ Import independence: Issues found")
    
    print(f"\nScore: {independence_score}/{max_score}")
    
    if independence_score == max_score:
        print("🎉 Project is fully independent and ready for relocation!")
    elif independence_score >= 3:
        print("✅ Project is mostly independent with minor issues")
    else:
        print("⚠️  Project has significant independence issues")
    
    return independence_score == max_score

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)