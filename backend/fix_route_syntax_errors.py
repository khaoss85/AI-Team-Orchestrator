#!/usr/bin/env python3
"""
Script to fix syntax errors in route files from trace support script
Task 1.4b - Fix syntax errors in route files da trace support script (20/28 files)

The original script added trace_id parameters in wrong positions causing:
"parameter without default follows parameter with default"
"""

import os
import ast
import logging
import re
from pathlib import Path
from typing import List, Tuple, Dict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_python_syntax(file_path: Path) -> Tuple[bool, str]:
    """Check if a Python file has valid syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to parse the file
        ast.parse(content)
        return True, ""
    except SyntaxError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Error reading file: {str(e)}"

def find_route_files_with_syntax_errors() -> List[Tuple[Path, str]]:
    """Find all route files with syntax errors"""
    routes_dir = Path(__file__).parent / "routes"
    error_files = []
    
    if not routes_dir.exists():
        logger.error(f"Routes directory not found: {routes_dir}")
        return []
    
    logger.info(f"🔍 Checking syntax in route files...")
    
    for route_file in routes_dir.glob("*.py"):
        if route_file.name == "__init__.py":
            continue
            
        is_valid, error_msg = check_python_syntax(route_file)
        if not is_valid:
            error_files.append((route_file, error_msg))
            logger.error(f"❌ {route_file.name}: {error_msg}")
        else:
            logger.info(f"✅ {route_file.name}: Syntax OK")
    
    return error_files

def fix_trace_id_parameter_syntax(content: str) -> Tuple[str, bool]:
    """Fix trace_id parameter placement in function definitions"""
    
    # Common problematic patterns that the original script might have created:
    # 1. trace_id: str = Depends(get_trace_id) added before required parameters
    # 2. trace_id added in wrong position in function signatures
    
    fixed_content = content
    changes_made = False
    
    # Pattern 1: Fix trace_id parameter placed before required parameters
    # Look for function definitions with trace_id before required params
    function_pattern = r'(async\s+)?def\s+\w+\s*\([^)]*trace_id[^)]*\):'
    
    lines = content.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        if re.search(function_pattern, line) and 'def ' in line:
            # Check if this line has the problematic pattern
            if 'trace_id' in line and '=' in line and 'Depends(' in line:
                # Try to fix the parameter order
                fixed_line = fix_function_signature(line)
                if fixed_line != line:
                    new_lines.append(fixed_line)
                    changes_made = True
                    logger.info(f"   Fixed function signature on line {i+1}")
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    if changes_made:
        fixed_content = '\n'.join(new_lines)
    
    # Pattern 2: Fix common FastAPI parameter ordering issues
    # Move trace_id with defaults to the end
    patterns_to_fix = [
        # Move trace_id with Depends to end of parameter list
        (r'(\w+)\s*:\s*(\w+),\s*trace_id:\s*str\s*=\s*Depends\([^)]+\),\s*([^)]+)\)', 
         r'\1: \2, \3, trace_id: str = Depends(get_trace_id))'),
        
        # Fix when trace_id is in middle with default before required param
        (r'(trace_id:\s*str\s*=\s*Depends\([^)]+\)),\s*(\w+:\s*\w+[^=][^,)]*)', 
         r'\2, \1'),
    ]
    
    for pattern, replacement in patterns_to_fix:
        old_content = fixed_content
        fixed_content = re.sub(pattern, replacement, fixed_content)
        if fixed_content != old_content:
            changes_made = True
            logger.info("   Applied parameter reordering fix")
    
    return fixed_content, changes_made

def fix_function_signature(line: str) -> str:
    """Fix a specific function signature line"""
    
    # Extract the function signature
    if not ('def ' in line and '(' in line and ')' in line):
        return line
    
    # Find the parameter list
    start_paren = line.find('(')
    end_paren = line.rfind(')')
    
    if start_paren == -1 or end_paren == -1:
        return line
    
    func_start = line[:start_paren + 1]
    func_end = line[end_paren:]
    params_str = line[start_paren + 1:end_paren]
    
    if not params_str.strip():
        return line
    
    # Split parameters
    params = []
    current_param = ""
    paren_depth = 0
    
    for char in params_str:
        if char == ',' and paren_depth == 0:
            params.append(current_param.strip())
            current_param = ""
        else:
            if char == '(':
                paren_depth += 1
            elif char == ')':
                paren_depth -= 1
            current_param += char
    
    if current_param.strip():
        params.append(current_param.strip())
    
    # Separate required and optional parameters
    required_params = []
    optional_params = []
    
    for param in params:
        param = param.strip()
        if not param:
            continue
            
        # Check if parameter has default value
        if '=' in param and not param.startswith('*'):
            # It's an optional parameter
            optional_params.append(param)
        else:
            # It's a required parameter
            required_params.append(param)
    
    # Reconstruct parameter list: required first, then optional
    new_params = required_params + optional_params
    new_params_str = ', '.join(new_params)
    
    new_line = func_start + new_params_str + func_end
    
    return new_line

def backup_file(file_path: Path) -> Path:
    """Create a backup of the file before fixing"""
    backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
    backup_path.write_text(file_path.read_text(encoding='utf-8'), encoding='utf-8')
    return backup_path

def fix_route_syntax_errors():
    """Main function to fix syntax errors in route files"""
    logger.info("🔧 Starting route files syntax error fix (Task 1.4b)")
    logger.info("=" * 60)
    
    # Find files with syntax errors
    error_files = find_route_files_with_syntax_errors()
    
    if not error_files:
        logger.info("✅ No syntax errors found in route files!")
        return True
    
    logger.info(f"\n🚨 Found {len(error_files)} files with syntax errors:")
    for file_path, error in error_files:
        logger.info(f"   - {file_path.name}: {error}")
    
    logger.info(f"\n🔧 Attempting to fix {len(error_files)} files...")
    
    fixed_count = 0
    failed_count = 0
    
    for file_path, error in error_files:
        logger.info(f"\n📝 Fixing {file_path.name}...")
        
        try:
            # Create backup
            backup_path = backup_file(file_path)
            logger.info(f"   📋 Backup created: {backup_path.name}")
            
            # Read original content
            original_content = file_path.read_text(encoding='utf-8')
            
            # Apply fixes
            fixed_content, changes_made = fix_trace_id_parameter_syntax(original_content)
            
            if changes_made:
                # Write fixed content
                file_path.write_text(fixed_content, encoding='utf-8')
                
                # Verify the fix worked
                is_valid, new_error = check_python_syntax(file_path)
                
                if is_valid:
                    logger.info(f"   ✅ {file_path.name} fixed successfully!")
                    fixed_count += 1
                else:
                    logger.error(f"   ❌ Fix failed for {file_path.name}: {new_error}")
                    # Restore backup
                    file_path.write_text(original_content, encoding='utf-8')
                    logger.info(f"   🔄 Restored original content")
                    failed_count += 1
            else:
                logger.warning(f"   ⚠️ No automatic fix available for {file_path.name}")
                logger.warning(f"   📋 Error: {error}")
                logger.warning(f"   🔧 Manual review required")
                failed_count += 1
                
        except Exception as e:
            logger.error(f"   ❌ Error fixing {file_path.name}: {e}")
            failed_count += 1
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("🎯 SYNTAX ERROR FIX SUMMARY")
    logger.info("=" * 60)
    logger.info(f"📊 Total files processed: {len(error_files)}")
    logger.info(f"✅ Successfully fixed: {fixed_count}")
    logger.info(f"❌ Failed to fix: {failed_count}")
    
    if failed_count == 0:
        logger.info("🎉 All syntax errors fixed successfully!")
        return True
    else:
        logger.warning(f"⚠️ {failed_count} files still need manual review")
        return False

def verify_all_routes_syntax():
    """Final verification that all route files have valid syntax"""
    logger.info("\n🔍 Final verification of all route files...")
    
    error_files = find_route_files_with_syntax_errors()
    
    if not error_files:
        logger.info("✅ All route files have valid syntax!")
        return True
    else:
        logger.error(f"❌ {len(error_files)} files still have syntax errors:")
        for file_path, error in error_files:
            logger.error(f"   - {file_path.name}: {error}")
        return False

if __name__ == "__main__":
    try:
        # Fix syntax errors
        success = fix_route_syntax_errors()
        
        # Final verification
        all_valid = verify_all_routes_syntax()
        
        if success and all_valid:
            logger.info("\n🎉 Task 1.4b completed successfully!")
            logger.info("✅ All route files now have valid syntax")
            exit(0)
        else:
            logger.error("\n❌ Task 1.4b needs manual intervention")
            logger.error("❌ Some files still have syntax errors")
            exit(1)
            
    except Exception as e:
        logger.error(f"❌ Script failed: {e}")
        exit(1)