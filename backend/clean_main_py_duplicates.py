#!/usr/bin/env python3
"""
Script to clean duplicate router includes and imports in main.py
Task 1.12 - Pulire duplicate router includes in main.py
"""

import re
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_main_py_duplicates():
    """Clean duplicate imports and router includes in main.py"""
    
    main_py_path = Path(__file__).parent / "main.py"
    
    if not main_py_path.exists():
        logger.error(f"main.py not found at {main_py_path}")
        return False
    
    # Read the current main.py
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    logger.info("🧹 Cleaning duplicate imports and router includes in main.py")
    
    # Fix 1: Remove duplicate TraceMiddleware import
    logger.info("1. Fixing duplicate TraceMiddleware imports")
    
    # Remove the duplicate import at line 13
    content = re.sub(
        r'\n# Import trace middleware for end-to-end traceability\nfrom middleware\.trace_middleware import TraceMiddleware, install_trace_aware_logging\n',
        '\n',
        content
    )
    
    # Fix 2: Remove duplicate TraceMiddleware middleware addition
    logger.info("2. Fixing duplicate TraceMiddleware middleware additions")
    
    # Remove the duplicate middleware addition
    lines = content.split('\n')
    new_lines = []
    trace_middleware_added = False
    
    for line in lines:
        if 'app.add_middleware(TraceMiddleware)' in line:
            if not trace_middleware_added:
                # Keep the first occurrence with comment
                new_lines.append("# Add X-Trace-ID middleware for end-to-end traceability")
                new_lines.append(line)
                trace_middleware_added = True
            else:
                # Skip duplicate
                logger.info("   - Removed duplicate TraceMiddleware middleware addition")
                continue
        else:
            new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    # Fix 3: Remove duplicate director_router includes
    logger.info("3. Fixing duplicate director_router includes")
    
    # Find and fix director_router duplicates
    lines = content.split('\n')
    new_lines = []
    director_router_added = False
    
    for line in lines:
        if 'app.include_router(director_router' in line:
            if not director_router_added:
                # Keep the first occurrence with prefix
                new_lines.append('app.include_router(director_router, prefix="/api")')
                director_router_added = True
                logger.info("   - Consolidated director_router to single include with /api prefix")
            else:
                # Skip duplicate
                logger.info("   - Removed duplicate director_router include")
                continue
        else:
            new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    # Fix 4: Consolidate service_registry routers
    logger.info("4. Consolidating service_registry routers")
    
    lines = content.split('\n')
    new_lines = []
    service_registry_handled = False
    
    for line in lines:
        if 'service_registry_router' in line or 'service_registry_compat_router' in line:
            if not service_registry_handled:
                # Add both routers with clear comments
                new_lines.append('# Service registry routes')
                new_lines.append('app.include_router(service_registry_router, prefix="/api")')
                new_lines.append('app.include_router(service_registry_compat_router)  # Legacy compatibility')
                service_registry_handled = True
                logger.info("   - Consolidated service_registry routers with clear prefixes")
            else:
                # Skip duplicate
                continue
        else:
            new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    # Fix 5: Consolidate component_health routers
    logger.info("5. Consolidating component_health routers")
    
    lines = content.split('\n')
    new_lines = []
    component_health_handled = False
    
    for line in lines:
        if 'component_health_router' in line or 'component_health_compat_router' in line:
            if not component_health_handled:
                # Add both routers with clear comments
                new_lines.append('# Component health routes')
                new_lines.append('app.include_router(component_health_router, prefix="/api")')
                new_lines.append('app.include_router(component_health_compat_router)  # Legacy compatibility')
                component_health_handled = True
                logger.info("   - Consolidated component_health routers with clear prefixes")
            else:
                # Skip duplicate
                continue
        else:
            new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    # Fix 6: Remove redundant comment before TraceMiddleware duplicate removal
    logger.info("6. Cleaning up redundant comments")
    
    # Remove duplicate comment about X-Trace-ID middleware
    content = re.sub(
        r'\n# Add X-Trace-ID middleware for end-to-end traceability\n# Add X-Trace-ID middleware for end-to-end traceability\n',
        '\n# Add X-Trace-ID middleware for end-to-end traceability\n',
        content
    )
    
    # Fix 7: Organize router includes with better structure
    logger.info("7. Organizing router includes with better structure")
    
    # Find the router includes section and reorganize
    router_section_start = content.find("# Include all routers")
    router_section_end = content.find("# Health check endpoint")
    
    if router_section_start != -1 and router_section_end != -1:
        before_routers = content[:router_section_start]
        after_routers = content[router_section_end:]
        
        # Create organized router includes
        organized_routers = """# Include all routers
# ==========================================

# Core workspace and project management
app.include_router(workspace_router)
app.include_router(director_router, prefix="/api")
app.include_router(agents_router)
app.include_router(tools_router)

# Goal and task management
app.include_router(goal_validation_router)
app.include_router(workspace_goals_router)
app.include_router(workspace_goals_direct_router)

# Asset and deliverable system
app.include_router(unified_assets_router)
app.include_router(assets_router, prefix="/api")
app.include_router(deliverables_router)

# Communication and feedback
app.include_router(websocket_router)
app.include_router(websocket_assets_router, prefix="/api")
app.include_router(conversation_router)
app.include_router(human_feedback_router)

# AI and processing
app.include_router(ai_content_router)
app.include_router(authentic_thinking_router, prefix="/api/thinking", tags=["thinking"])
app.include_router(thinking_router, prefix="/api")
app.include_router(memory_router, prefix="/api")

# Monitoring and system management
app.include_router(monitoring_router)
app.include_router(system_monitoring_router)
app.include_router(project_insights_router)
app.include_router(improvement_router)

# Service management
app.include_router(service_registry_router, prefix="/api")
app.include_router(service_registry_compat_router)  # Legacy compatibility
app.include_router(component_health_router, prefix="/api")
app.include_router(component_health_compat_router)  # Legacy compatibility

# Workflow and delegation
app.include_router(proposals_router)
app.include_router(delegation_router)

# Documentation and utilities
app.include_router(documents_router)
app.include_router(utils_router)

# API compatibility layer
app.include_router(api_router)

"""
        
        content = before_routers + organized_routers + after_routers
        logger.info("   - Organized router includes into logical groups")
    
    # Check if changes were made
    if content != original_content:
        # Write the cleaned content back
        with open(main_py_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("✅ main.py cleaned successfully")
        
        # Log the changes made
        original_lines = len(original_content.split('\n'))
        new_lines = len(content.split('\n'))
        
        logger.info(f"📊 Changes summary:")
        logger.info(f"   - Original lines: {original_lines}")
        logger.info(f"   - New lines: {new_lines}")
        logger.info(f"   - Lines reduced: {original_lines - new_lines}")
        logger.info(f"   - Duplicate imports removed: ✅")
        logger.info(f"   - Duplicate middleware removed: ✅") 
        logger.info(f"   - Duplicate router includes removed: ✅")
        logger.info(f"   - Router organization improved: ✅")
        
        return True
    else:
        logger.info("ℹ️ No changes needed - main.py is already clean")
        return True

if __name__ == "__main__":
    success = clean_main_py_duplicates()
    if success:
        print("✅ main.py cleanup completed successfully")
    else:
        print("❌ main.py cleanup failed")
        exit(1)