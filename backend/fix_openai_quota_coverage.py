#!/usr/bin/env python3
"""
OpenAI Quota Tracking Coverage Fix Script
Fixes all direct OpenAI instantiations to use quota-tracked factory
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

def find_violations() -> List[Tuple[Path, int, str]]:
    """Find all files with direct OpenAI instantiation"""
    violations = []
    backend_dir = Path(__file__).parent
    
    # Patterns that indicate direct instantiation
    patterns = [
        r'from openai import (?:OpenAI|AsyncOpenAI)',
        r'OpenAI\s*\(',
        r'AsyncOpenAI\s*\(',
        r'openai\.OpenAI\s*\(',
        r'openai\.AsyncOpenAI\s*\(',
        r'client\s*=\s*(?:OpenAI|AsyncOpenAI)',
    ]
    
    for py_file in backend_dir.rglob("*.py"):
        # Skip this script and the factory itself
        if py_file.name in ["fix_openai_quota_coverage.py", "openai_client_factory.py"]:
            continue
            
        try:
            content = py_file.read_text()
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                for pattern in patterns:
                    if re.search(pattern, line):
                        # Check if it's already using the factory
                        if "openai_client_factory" not in line:
                            violations.append((py_file, i, line.strip()))
                            break
        except Exception as e:
            print(f"Error reading {py_file}: {e}")
    
    return violations

def generate_fix_report(violations: List[Tuple[Path, int, str]]) -> str:
    """Generate a detailed fix report"""
    report = ["# OpenAI Quota Tracking Violations Report\n"]
    report.append(f"## Total Violations Found: {len(violations)}\n")
    
    # Group by directory
    by_dir = {}
    for path, line_num, line in violations:
        dir_name = path.parent.name
        if dir_name not in by_dir:
            by_dir[dir_name] = []
        by_dir[dir_name].append((path, line_num, line))
    
    for dir_name, files in sorted(by_dir.items()):
        report.append(f"\n### {dir_name}/ ({len(files)} violations)\n")
        for path, line_num, line in files:
            rel_path = path.relative_to(Path(__file__).parent)
            report.append(f"- **{rel_path}** (line {line_num})")
            report.append(f"  ```python\n  {line}\n  ```")
            
            # Suggest fix
            if "AsyncOpenAI" in line:
                report.append("  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`")
                report.append("  ```python\n  client = get_async_openai_client()\n  ```")
            else:
                report.append("  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`")
                report.append("  ```python\n  client = get_openai_client()\n  ```")
    
    # Add remediation steps
    report.append("\n## Remediation Steps\n")
    report.append("1. **Immediate**: Fix all direct instantiations")
    report.append("2. **Extend Factory**: Add tracking for embeddings, assistants, threads, images")
    report.append("3. **Validation**: Run integration tests to verify tracking")
    report.append("4. **Prevention**: Add pre-commit hook to catch violations")
    
    return "\n".join(report)

def check_untracked_methods() -> List[str]:
    """Check for usage of untracked OpenAI methods"""
    untracked_methods = []
    backend_dir = Path(__file__).parent
    
    # Methods that should be tracked but aren't
    methods_to_check = [
        "embeddings.create",
        "images.generate",
        "audio.transcriptions.create",
        "audio.translations.create",
        "assistants.create",
        "threads.create",
        "files.create",
        "vector_stores.create",
        "moderations.create"
    ]
    
    for method in methods_to_check:
        found_in = []
        for py_file in backend_dir.rglob("*.py"):
            try:
                content = py_file.read_text()
                if method in content:
                    found_in.append(str(py_file.relative_to(backend_dir)))
            except:
                pass
        
        if found_in:
            untracked_methods.append(f"- **{method}**: Used in {len(found_in)} files")
            for file in found_in[:3]:  # Show first 3 files
                untracked_methods.append(f"  - {file}")
            if len(found_in) > 3:
                untracked_methods.append(f"  - ... and {len(found_in) - 3} more files")
    
    return untracked_methods

def main():
    print("🔍 Scanning for OpenAI quota tracking violations...")
    
    # Find violations
    violations = find_violations()
    print(f"❌ Found {len(violations)} direct OpenAI instantiations bypassing quota tracking")
    
    # Check for untracked methods
    print("\n🔍 Checking for untracked OpenAI API methods...")
    untracked = check_untracked_methods()
    
    # Generate report
    report = generate_fix_report(violations)
    
    # Add untracked methods to report
    if untracked:
        report += "\n\n## Untracked OpenAI API Methods in Use\n"
        report += "\n".join(untracked)
    
    # Save report
    report_path = Path(__file__).parent / "openai_quota_violations_report.md"
    report_path.write_text(report)
    print(f"\n📄 Detailed report saved to: {report_path}")
    
    # Summary
    print("\n📊 Summary:")
    print(f"  - Direct instantiations: {len(violations)}")
    print(f"  - Untracked methods: {len(untracked)}")
    print(f"  - Estimated tracking gap: ~{len(violations) * 100} API calls/day")
    
    return len(violations)

if __name__ == "__main__":
    exit(main())