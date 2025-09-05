#!/usr/bin/env python3
"""
Pre-commit hook to prevent OpenAI quota tracking bypasses
Blocks commits that introduce direct OpenAI instantiation
"""

import re
import sys
from pathlib import Path

def check_file_for_violations(file_path: str) -> list:
    """Check a single file for OpenAI compliance violations"""
    violations = []
    
    # Patterns that indicate quota bypass
    violation_patterns = [
        (r'OpenAI\(\)', 'Direct OpenAI() instantiation detected'),
        (r'AsyncOpenAI\(\)', 'Direct AsyncOpenAI() instantiation detected'),  
        (r'openai\.OpenAI\(\)', 'Direct openai.OpenAI() instantiation detected'),
        (r'openai\.AsyncOpenAI\(\)', 'Direct openai.AsyncOpenAI() instantiation detected'),
        (r'from openai import.*OpenAI(?!.*factory)', 'Direct OpenAI import without factory detected'),
    ]
    
    # Allowed patterns (won't trigger violations)
    allowed_patterns = [
        r'openai_client_factory',
        r'get_enhanced_openai_client',
        r'get_enhanced_async_openai_client',
        r'# APPROVED:',  # Allow if explicitly approved with comment
    ]
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line_num, line in enumerate(lines, 1):
            # Skip if line contains allowed patterns
            if any(re.search(pattern, line) for pattern in allowed_patterns):
                continue
                
            # Check for violations
            for pattern, message in violation_patterns:
                if re.search(pattern, line):
                    violations.append({
                        'line': line_num,
                        'content': line.strip(),
                        'message': message
                    })
                    
    except Exception as e:
        violations.append({
            'line': 0,
            'content': '',
            'message': f'Error reading file: {e}'
        })
    
    return violations

def main():
    """Main pre-commit validation"""
    # Get files from command line arguments
    files_to_check = sys.argv[1:] if len(sys.argv) > 1 else []
    
    if not files_to_check:
        # If no specific files, check all staged Python files
        import subprocess
        try:
            result = subprocess.run(['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'], 
                                  capture_output=True, text=True)
            files_to_check = [f for f in result.stdout.strip().split('\n') 
                            if f.endswith('.py') and f]
        except:
            print("❌ Could not get staged files from git")
            sys.exit(1)
    
    # Check each file
    total_violations = 0
    
    for file_path in files_to_check:
        if not Path(file_path).exists():
            continue
            
        violations = check_file_for_violations(file_path)
        
        if violations:
            total_violations += len(violations)
            print(f"🚨 QUOTA BYPASS DETECTED: {file_path}")
            
            for violation in violations:
                print(f"  Line {violation['line']:3d}: {violation['message']}")
                print(f"             {violation['content']}")
            print()
    
    if total_violations > 0:
        print(f"❌ COMMIT BLOCKED: {total_violations} quota tracking bypass(es) detected!")
        print()
        print("🔧 To fix:")
        print("1. Replace OpenAI() with get_enhanced_openai_client(workspace_id=...)")
        print("2. Replace AsyncOpenAI() with get_enhanced_async_openai_client(workspace_id=...)")
        print("3. Import from utils.openai_client_factory_enhanced")
        print("4. Add '# APPROVED:' comment if bypass is intentional")
        print()
        print("💡 Run 'python backend/migrate_openai_factory.py' for automatic migration")
        
        sys.exit(1)
    
    print("✅ OpenAI quota tracking compliance verified")
    sys.exit(0)

if __name__ == "__main__":
    main()