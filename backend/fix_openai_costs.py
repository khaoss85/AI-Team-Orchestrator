#!/usr/bin/env python3
"""
Automated OpenAI Cost Reduction Script
Reduces API costs by 94% through strategic model downgrades
"""

import sys
import re
from pathlib import Path
from typing import List, Tuple
import argparse

# Define the replacements needed
REPLACEMENTS = [
    {
        "file": "ai_agents/director.py",
        "description": "Director agent models (14 instances)",
        "changes": [
            ('"model": "gpt-4o"', '"model": "gpt-4o-mini"'),
        ],
        "estimated_savings": 10.00
    },
    {
        "file": "services/universal_learning_engine.py",
        "description": "Universal Learning Engine insight extraction",
        "changes": [
            ('"model": "gpt-4o"', '"model": "gpt-4o-mini"'),  # Line 239
        ],
        "line_numbers": [239],  # Only change line 239, not others
        "estimated_savings": 0.50
    },
    {
        "file": "services/goal_progress_auto_recovery.py", 
        "description": "Auto-recovery check interval",
        "changes": [
            ("self.check_interval_seconds = 300", "self.check_interval_seconds = 1800"),
        ],
        "estimated_savings": 0.07
    },
    {
        "file": "tools/workspace_service.py",
        "description": "Workspace service model",
        "changes": [
            ('"model": "gpt-4"', '"model": "gpt-4o-mini"'),
        ],
        "estimated_savings": 0.40
    },
    {
        "file": "tools/enhanced_document_search.py",
        "description": "Document search model",
        "changes": [
            ('model="gpt-4"', 'model="gpt-4o-mini"'),
        ],
        "estimated_savings": 0.40
    },
    {
        "file": "ai_agents/conversational.py",
        "description": "Conversational agent model",
        "changes": [
            ('model="gpt-4"', 'model="gpt-4o-mini"'),
        ],
        "estimated_savings": 0.50
    },
    {
        "file": "utils/context_manager.py",
        "description": "Context manager model",
        "changes": [
            ('model="gpt-4"', 'model="gpt-4o-mini"'),
        ],
        "estimated_savings": 0.30
    },
    {
        "file": "config/knowledge_insights_config.py",
        "description": "Knowledge insights default model",
        "changes": [
            ('default="gpt-4"', 'default="gpt-4o-mini"'),
            ('"gpt-4")', '"gpt-4o-mini")'),
        ],
        "estimated_savings": 0.30
    }
]

def backup_file(filepath: Path) -> Path:
    """Create a backup of the file before modification"""
    backup_path = filepath.with_suffix(filepath.suffix + '.backup')
    backup_path.write_text(filepath.read_text())
    return backup_path

def apply_replacements(filepath: Path, changes: List[Tuple[str, str]], 
                      line_numbers: List[int] = None) -> int:
    """Apply replacements to a file"""
    content = filepath.read_text()
    original_content = content
    changes_made = 0
    
    if line_numbers:
        # Apply changes only to specific lines
        lines = content.split('\n')
        for line_num in line_numbers:
            if 0 < line_num <= len(lines):
                line_idx = line_num - 1
                for old, new in changes:
                    if old in lines[line_idx]:
                        lines[line_idx] = lines[line_idx].replace(old, new)
                        changes_made += 1
        content = '\n'.join(lines)
    else:
        # Apply changes throughout the file
        for old, new in changes:
            count = content.count(old)
            content = content.replace(old, new)
            changes_made += count
    
    if content != original_content:
        filepath.write_text(content)
    
    return changes_made

def main():
    parser = argparse.ArgumentParser(description="Fix OpenAI API cost issues")
    parser.add_argument("--apply", action="store_true", 
                       help="Actually apply the changes (without this, runs in dry-run mode)")
    parser.add_argument("--restore", action="store_true",
                       help="Restore from backup files")
    args = parser.parse_args()
    
    backend_dir = Path("/Users/pelleri/Documents/ai-team-orchestrator/backend")
    
    if args.restore:
        print("🔄 Restoring from backups...")
        restored = 0
        for item in REPLACEMENTS:
            filepath = backend_dir / item["file"]
            backup_path = filepath.with_suffix(filepath.suffix + '.backup')
            if backup_path.exists():
                filepath.write_text(backup_path.read_text())
                print(f"  ✅ Restored: {item['file']}")
                restored += 1
        print(f"\n✅ Restored {restored} files")
        return
    
    print("=" * 80)
    print("OpenAI API Cost Reduction Script")
    print("=" * 80)
    
    if not args.apply:
        print("\n⚠️  DRY RUN MODE - No changes will be made")
        print("   Add --apply flag to actually make changes\n")
    
    total_savings = 0
    total_changes = 0
    
    for item in REPLACEMENTS:
        filepath = backend_dir / item["file"]
        
        if not filepath.exists():
            print(f"❌ File not found: {item['file']}")
            continue
        
        print(f"\n📁 {item['file']}")
        print(f"   {item['description']}")
        print(f"   Estimated savings: ${item['estimated_savings']:.2f}/day")
        
        if args.apply:
            # Create backup
            backup_path = backup_file(filepath)
            print(f"   📦 Backup created: {backup_path.name}")
            
            # Apply changes
            line_numbers = item.get("line_numbers")
            changes = apply_replacements(filepath, item["changes"], line_numbers)
            
            if changes > 0:
                print(f"   ✅ Applied {changes} changes")
                total_savings += item["estimated_savings"]
                total_changes += changes
            else:
                print(f"   ⚠️  No changes needed")
        else:
            # Dry run - just count potential changes
            content = filepath.read_text()
            potential_changes = 0
            for old, new in item["changes"]:
                potential_changes += content.count(old)
            
            if potential_changes > 0:
                print(f"   🔍 Would make {potential_changes} changes")
                total_savings += item["estimated_savings"]
                total_changes += potential_changes
            else:
                print(f"   ⚠️  No changes needed")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if args.apply:
        print(f"✅ Changes applied: {total_changes}")
    else:
        print(f"🔍 Changes that would be made: {total_changes}")
    
    print(f"💰 Estimated daily savings: ${total_savings:.2f}")
    print(f"📅 Estimated monthly savings: ${total_savings * 30:.2f}")
    print(f"📊 Percentage reduction: {(total_savings / 13.21) * 100:.1f}%")
    
    if not args.apply:
        print("\n⚡ To apply these changes, run:")
        print("   python3 fix_openai_costs.py --apply")
    else:
        print("\n✅ All changes have been applied!")
        print("📝 Backup files created with .backup extension")
        print("🔄 To restore, run: python3 fix_openai_costs.py --restore")
        
        print("\n⚠️  IMPORTANT NEXT STEPS:")
        print("1. Restart the backend service")
        print("2. Monitor the OpenAI dashboard for cost reduction")
        print("3. Test key features to ensure they still work")
        print("4. Deploy to production if tests pass")

if __name__ == "__main__":
    main()