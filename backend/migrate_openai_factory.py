#!/usr/bin/env python3
"""
Emergency OpenAI Factory Migration Script
Automatically migrates all files from direct OpenAI instantiation to enhanced factory pattern
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict

def find_openai_violations(directory: str) -> List[Tuple[str, int, str]]:
    """Find all OpenAI direct instantiations in the codebase"""
    violations = []
    
    # Patterns to search for
    patterns = [
        r'from openai import.*OpenAI',
        r'import openai',
        r'OpenAI\(\)',
        r'AsyncOpenAI\(\)',
        r'openai\.OpenAI\(\)',
        r'openai\.AsyncOpenAI\(\)',
    ]
    
    # Files to search
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip certain directories
        skip_dirs = {'.git', '__pycache__', '.pytest_cache', 'node_modules', '.env'}
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for line_num, line in enumerate(lines, 1):
                for pattern in patterns:
                    if re.search(pattern, line):
                        violations.append((file_path, line_num, line.strip()))
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
    
    return violations

def migrate_file(file_path: str) -> bool:
    """Migrate a single file to use enhanced factory"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Migration patterns
        migrations = [
            # Direct imports
            (
                r'from openai import OpenAI, AsyncOpenAI',
                'from utils.openai_client_factory_enhanced import get_enhanced_openai_client, get_enhanced_async_openai_client'
            ),
            (
                r'from openai import OpenAI',
                'from utils.openai_client_factory_enhanced import get_enhanced_openai_client'
            ),
            (
                r'from openai import AsyncOpenAI',
                'from utils.openai_client_factory_enhanced import get_enhanced_async_openai_client'
            ),
            (
                r'import openai',
                'from utils.openai_client_factory_enhanced import get_enhanced_openai_client, get_enhanced_async_openai_client'
            ),
            
            # Direct instantiations
            (
                r'OpenAI\(\)',
                'get_enhanced_openai_client(workspace_id=workspace_id)'
            ),
            (
                r'AsyncOpenAI\(\)',
                'get_enhanced_async_openai_client(workspace_id=workspace_id)'
            ),
            (
                r'openai\.OpenAI\(\)',
                'get_enhanced_openai_client(workspace_id=workspace_id)'
            ),
            (
                r'openai\.AsyncOpenAI\(\)',
                'get_enhanced_async_openai_client(workspace_id=workspace_id)'
            ),
            
            # API key variations
            (
                r'OpenAI\(api_key=([^)]+)\)',
                r'get_enhanced_openai_client(api_key=\1, workspace_id=workspace_id)'
            ),
            (
                r'AsyncOpenAI\(api_key=([^)]+)\)',
                r'get_enhanced_async_openai_client(api_key=\1, workspace_id=workspace_id)'
            ),
        ]
        
        # Apply migrations
        for pattern, replacement in migrations:
            content = re.sub(pattern, replacement, content)
        
        # Only write if content changed
        if content != original_content:
            # Create backup
            backup_path = file_path + '.backup'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Write migrated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Migrated: {file_path}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Failed to migrate {file_path}: {e}")
        return False

def create_workspace_id_injector(file_path: str) -> str:
    """Analyze file and suggest workspace_id injection method"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Common patterns for workspace_id availability
        if 'self.workspace_id' in content:
            return 'self.workspace_id'
        elif 'workspace_id=' in content:
            return 'workspace_id'
        elif 'def ' in content and 'workspace_id' in content:
            return 'workspace_id (function parameter)'
        else:
            return '"global" (fallback)'
    except:
        return '"global" (fallback)'

def main():
    """Main migration function"""
    print("🚨 OpenAI Factory Emergency Migration")
    print("=" * 50)
    
    # Find all violations
    backend_dir = os.path.dirname(__file__)
    violations = find_openai_violations(backend_dir)
    
    if not violations:
        print("✅ No OpenAI violations found!")
        return
    
    print(f"🔍 Found {len(violations)} violations:")
    
    # Group by file
    files_with_violations = {}
    for file_path, line_num, line in violations:
        if file_path not in files_with_violations:
            files_with_violations[file_path] = []
        files_with_violations[file_path].append((line_num, line))
    
    # Show violations
    for file_path, violation_lines in files_with_violations.items():
        rel_path = os.path.relpath(file_path, backend_dir)
        print(f"\n📁 {rel_path}")
        for line_num, line in violation_lines:
            print(f"  {line_num:3d}: {line}")
    
    print(f"\n🎯 Ready to migrate {len(files_with_violations)} files")
    
    # Ask for confirmation
    response = input("\nProceed with migration? (y/N): ").lower().strip()
    if response != 'y':
        print("❌ Migration cancelled")
        return
    
    # Migrate files
    print("\n🔄 Starting migration...")
    migrated_count = 0
    
    for file_path in files_with_violations.keys():
        if migrate_file(file_path):
            migrated_count += 1
            # Show workspace_id suggestion
            workspace_id_method = create_workspace_id_injector(file_path)
            print(f"   💡 Suggested workspace_id: {workspace_id_method}")
    
    print(f"\n✅ Migration complete!")
    print(f"   📊 {migrated_count}/{len(files_with_violations)} files migrated")
    print(f"   📁 Backups created with .backup extension")
    
    # Show next steps
    print(f"\n🚀 Next Steps:")
    print(f"1. Review migrated files and fix workspace_id parameters")
    print(f"2. Test the application to ensure everything works")
    print(f"3. Remove .backup files once confirmed working")
    print(f"4. Add pre-commit hooks to prevent future violations")

if __name__ == "__main__":
    main()