#!/usr/bin/env python3
"""
Script to complete trace_id support implementation in remaining route files
Task 1.4b - Fix syntax errors in route files da trace support script (20/28 files)

Actually adds proper trace_id support to the remaining route files that don't have it yet.
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Tuple, Set

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_route_files_status() -> Tuple[List[Path], List[Path]]:
    """Get lists of route files with and without trace_id support"""
    routes_dir = Path(__file__).parent / "routes"
    
    with_trace = []
    without_trace = []
    
    for route_file in routes_dir.glob("*.py"):
        if route_file.name == "__init__.py":
            continue
            
        try:
            content = route_file.read_text(encoding='utf-8')
            if 'trace_id' in content and 'get_trace_id' in content:
                with_trace.append(route_file)
            else:
                without_trace.append(route_file)
        except Exception as e:
            logger.error(f"Error reading {route_file}: {e}")
            without_trace.append(route_file)
    
    return with_trace, without_trace

def add_trace_middleware_imports(content: str) -> Tuple[str, bool]:
    """Add trace middleware imports if not present"""
    if 'from middleware.trace_middleware import' in content:
        return content, False
    
    # Find where to insert the imports (after fastapi imports)
    lines = content.split('\n')
    insert_index = 0
    
    # Look for a good place to insert after FastAPI imports
    for i, line in enumerate(lines):
        if line.strip().startswith('from fastapi import'):
            insert_index = i + 1
        elif line.strip().startswith('from typing import'):
            insert_index = max(insert_index, i + 1)
    
    # Insert the trace middleware imports
    trace_import = "from middleware.trace_middleware import get_trace_id, create_traced_logger, TracedDatabaseOperation"
    
    if insert_index == 0:
        # Insert at the beginning after any existing imports
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('from') and not line.strip().startswith('import'):
                insert_index = i
                break
    
    # Insert the import
    lines.insert(insert_index, trace_import)
    
    return '\n'.join(lines), True

def add_request_parameter_to_functions(content: str) -> Tuple[str, bool]:
    """Add Request parameter to route functions that don't have it"""
    changes_made = False
    
    # Find route functions (@router.get, @router.post, etc.)
    lines = content.split('\n')
    new_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this is a route decorator
        if re.match(r'\s*@router\.(get|post|put|delete|patch)', line.strip()):
            # Look for the function definition on the next lines
            func_line_index = None
            for j in range(i + 1, min(i + 5, len(lines))):
                if re.match(r'\s*async\s+def\s+\w+', lines[j].strip()) or re.match(r'\s*def\s+\w+', lines[j].strip()):
                    func_line_index = j
                    break
            
            if func_line_index is not None:
                func_line = lines[func_line_index]
                
                # Check if Request parameter is already present
                if 'request: Request' not in func_line:
                    # Add Request parameter
                    updated_func_line = add_request_to_function_signature(func_line)
                    if updated_func_line != func_line:
                        lines[func_line_index] = updated_func_line
                        changes_made = True
                        logger.info(f"   Added Request parameter to function on line {func_line_index + 1}")
        
        i += 1
    
    if changes_made:
        content = '\n'.join(lines)
    
    return content, changes_made

def add_request_to_function_signature(func_line: str) -> str:
    """Add Request parameter to a function signature"""
    
    # Extract function signature parts
    if 'def ' not in func_line or '(' not in func_line:
        return func_line
    
    # Find the parameter list
    start_paren = func_line.find('(')
    end_paren = func_line.rfind(')')
    
    if start_paren == -1 or end_paren == -1:
        return func_line
    
    func_start = func_line[:start_paren + 1]
    func_end = func_line[end_paren:]
    params_str = func_line[start_paren + 1:end_paren].strip()
    
    # Add Request parameter at the end
    if params_str:
        # Add comma and Request parameter
        new_params = f"{params_str}, request: Request"
    else:
        # First parameter
        new_params = "request: Request"
    
    return func_start + new_params + func_end

def add_trace_logging_to_functions(content: str) -> Tuple[str, bool]:
    """Add trace logging to route functions"""
    changes_made = False
    
    lines = content.split('\n')
    new_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        
        # Check if this is a route function definition
        if (re.match(r'\s*async\s+def\s+\w+.*request:\s*Request', line) or 
            re.match(r'\s*def\s+\w+.*request:\s*Request', line)):
            
            # Extract function name
            func_match = re.search(r'def\s+(\w+)', line)
            if func_match:
                func_name = func_match.group(1)
                
                # Look for the docstring or first line of function body
                body_start_index = i + 1
                while (body_start_index < len(lines) and 
                       (lines[body_start_index].strip().startswith('"""') or 
                        lines[body_start_index].strip().startswith("'''") or
                        not lines[body_start_index].strip())):
                    body_start_index += 1
                
                # Check if trace logging is already present
                if body_start_index < len(lines):
                    next_few_lines = '\n'.join(lines[body_start_index:body_start_index + 3])
                    if 'get_trace_id' not in next_few_lines:
                        # Add trace logging
                        indent = '    '  # Standard 4-space indent
                        trace_lines = [
                            f"{indent}# Get trace ID and create traced logger",
                            f"{indent}trace_id = get_trace_id(request)",
                            f"{indent}logger = create_traced_logger(request, __name__)",
                            f"{indent}logger.info(f\"Route {func_name} called\", endpoint=\"{func_name}\", trace_id=trace_id)",
                            ""
                        ]
                        
                        # Insert trace lines after function definition
                        for j, trace_line in enumerate(trace_lines):
                            new_lines.append(trace_line)
                        
                        changes_made = True
                        logger.info(f"   Added trace logging to function {func_name}")
        
        i += 1
    
    if changes_made:
        content = '\n'.join(new_lines)
    
    return content, changes_made

def ensure_request_import(content: str) -> Tuple[str, bool]:
    """Ensure Request is imported from FastAPI"""
    
    # Check if Request is already imported
    if 'Request' in content and 'from fastapi import' in content:
        # Check if Request is in the FastAPI import
        fastapi_import_match = re.search(r'from fastapi import ([^\\n]+)', content)
        if fastapi_import_match:
            imports = fastapi_import_match.group(1)
            if 'Request' in imports:
                return content, False
    
    # Need to add Request to FastAPI imports
    fastapi_pattern = r'(from fastapi import )([^\\n]+)'
    
    def add_request_to_import(match):
        prefix = match.group(1)
        current_imports = match.group(2)
        
        if 'Request' not in current_imports:
            # Add Request to the imports
            if current_imports.strip():
                return f"{prefix}Request, {current_imports}"
            else:
                return f"{prefix}Request"
        return match.group(0)
    
    new_content = re.sub(fastapi_pattern, add_request_to_import, content)
    
    return new_content, new_content != content

def add_trace_support_to_file(file_path: Path) -> bool:
    """Add complete trace support to a route file"""
    logger.info(f"📝 Adding trace support to {file_path.name}")
    
    try:
        # Read original content
        original_content = file_path.read_text(encoding='utf-8')
        content = original_content
        
        changes_made = False
        
        # Step 1: Ensure Request is imported
        content, changed = ensure_request_import(content)
        if changed:
            changes_made = True
            logger.info("   ✅ Added Request import")
        
        # Step 2: Add trace middleware imports
        content, changed = add_trace_middleware_imports(content)
        if changed:
            changes_made = True
            logger.info("   ✅ Added trace middleware imports")
        
        # Step 3: Add Request parameter to functions
        content, changed = add_request_parameter_to_functions(content)
        if changed:
            changes_made = True
            logger.info("   ✅ Added Request parameters to functions")
        
        # Step 4: Add trace logging to functions
        content, changed = add_trace_logging_to_functions(content)
        if changed:
            changes_made = True
            logger.info("   ✅ Added trace logging to functions")
        
        if changes_made:
            # Create backup
            backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
            backup_path.write_text(original_content, encoding='utf-8')
            
            # Write updated content
            file_path.write_text(content, encoding='utf-8')
            
            logger.info(f"   ✅ {file_path.name} updated successfully")
            return True
        else:
            logger.info(f"   ℹ️ {file_path.name} already has trace support or no changes needed")
            return True
            
    except Exception as e:
        logger.error(f"   ❌ Error updating {file_path.name}: {e}")
        return False

def complete_trace_id_support():
    """Main function to complete trace_id support in all route files"""
    logger.info("🎯 Completing trace_id support in route files (Task 1.4b)")
    logger.info("=" * 60)
    
    # Get current status
    with_trace, without_trace = get_route_files_status()
    
    logger.info(f"📊 Current status:")
    logger.info(f"   ✅ Files with trace support: {len(with_trace)}")
    logger.info(f"   ⏳ Files needing trace support: {len(without_trace)}")
    
    if not without_trace:
        logger.info("✅ All route files already have trace support!")
        return True
    
    logger.info(f"\n🔧 Adding trace support to {len(without_trace)} files...")
    
    # Sort files by name for consistent processing
    without_trace.sort(key=lambda x: x.name)
    
    success_count = 0
    failed_count = 0
    
    for file_path in without_trace:
        if add_trace_support_to_file(file_path):
            success_count += 1
        else:
            failed_count += 1
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("🎯 TRACE SUPPORT COMPLETION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"📊 Files processed: {len(without_trace)}")
    logger.info(f"✅ Successfully updated: {success_count}")
    logger.info(f"❌ Failed to update: {failed_count}")
    
    # Final status check
    with_trace_final, without_trace_final = get_route_files_status()
    logger.info(f"\n📊 Final status:")
    logger.info(f"   ✅ Files with trace support: {len(with_trace_final)}")
    logger.info(f"   ⏳ Files still needing trace support: {len(without_trace_final)}")
    
    if len(without_trace_final) == 0:
        logger.info("🎉 All route files now have trace support!")
        return True
    else:
        logger.warning(f"⚠️ {len(without_trace_final)} files still need manual review")
        for file_path in without_trace_final:
            logger.warning(f"   - {file_path.name}")
        return False

if __name__ == "__main__":
    try:
        success = complete_trace_id_support()
        
        if success:
            logger.info("\n🎉 Task 1.4b completed successfully!")
            logger.info("✅ All route files now have trace_id support")
            exit(0)
        else:
            logger.error("\n❌ Task 1.4b needs manual intervention")
            logger.error("❌ Some files still need trace support")
            exit(1)
            
    except Exception as e:
        logger.error(f"❌ Script failed: {e}")
        exit(1)