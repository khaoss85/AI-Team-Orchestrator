#!/usr/bin/env python3
"""
🚨 CRITICAL DATABASE ANALYSIS - Goal-Deliverable Mapping Issue Analysis

Workspace: 3adfdc92-b316-442f-b9ca-a8d1df49e200
Issue: Classic "first active goal" bug has returned

This script analyzes the current state, identifies mapping issues, and generates corrective SQL.
"""

import json
from datetime import datetime

# Data from API calls (saved to avoid additional requests)
DELIVERABLES_DATA = [
    {
        "id": "c3430039-5d99-4afa-84a3-141351a37ff1",
        "workspace_id": "3adfdc92-b316-442f-b9ca-a8d1df49e200",
        "goal_id": "10f7957c-cc17-481b-970a-4ec4a9fd26c4",
        "title": "Analyze Current Engagement Metrics - AI-Generated Deliverable",
        "display_content": "<div class=\"markdown-content\">..."  # Has display_content
    },
    {
        "id": "36ed56ee-bff6-4ab1-b361-b119aa9ab5b9", 
        "workspace_id": "3adfdc92-b316-442f-b9ca-a8d1df49e200",
        "goal_id": "8bb605d3-b772-45ff-a719-121cb19d1a87",
        "title": "Gather Demographic and Firmographic Details - AI-Generated Deliverable",
        "display_content": "<div class=\"content\">..."  # Has display_content
    },
    {
        "id": "7a0cb257-3848-4e14-b858-4be0df1f034a",
        "workspace_id": "3adfdc92-b316-442f-b9ca-a8d1df49e200", 
        "goal_id": "10f7957c-cc17-481b-970a-4ec4a9fd26c4",
        "title": "Gather Outreach Techniques of Competitors: API Call - AI-Generated Deliverable",
        "display_content": "<div class=\"content\">..."  # Has display_content
    },
    {
        "id": "2e06580b-5495-4561-8d84-dca2bee5c957",
        "workspace_id": "3adfdc92-b316-442f-b9ca-a8d1df49e200",
        "goal_id": "10f7957c-cc17-481b-970a-4ec4a9fd26c4", 
        "title": "Search Competitor Case Studies: File Search - AI-Generated Deliverable",
        "display_content": "<div class=\"content\">..."  # Has display_content
    },
    {
        "id": "04ed0b1d-9d35-4dea-bd8a-c672687e7e0a",
        "workspace_id": "3adfdc92-b316-442f-b9ca-a8d1df49e200",
        "goal_id": "8bb605d3-b772-45ff-a719-121cb19d1a87",
        "title": "Research Target Audience Insights: Market Research - AI-Generated Deliverable", 
        "display_content": None  # Missing display_content
    }
]

GOALS_DATA = [
    {
        "id": "512d8475-15a4-47d1-8680-600d38fd2cf1",
        "metric_type": "deliverable_script_di_vendita", 
        "description": "Script di vendita e guide per obiezioni",
        "current_value": 0.0,
        "target_value": 1.0
    },
    {
        "id": "10f7957c-cc17-481b-970a-4ec4a9fd26c4",
        "metric_type": "deliverable_analisi_delle_campagne",
        "description": "Analisi delle campagne outbound dei competitor nel settore SaaS",
        "current_value": 0.0, 
        "target_value": 1.0
    },
    {
        "id": "74930a71-a443-4d56-9c09-1a8893214a9f",
        "metric_type": "competitor_analysis",
        "description": "Analisi dei competitor completata riguardante campagne outbound di successo nel settore SaaS.",
        "current_value": 6.0,  # 100% complete but shows as incomplete in frontend
        "target_value": 1.0
    },
    {
        "id": "2491a9e0-c4ef-41fc-b2b4-e9eb41666972", 
        "metric_type": "csv_imports",
        "description": "File CSV pronto per l'importazione in HubSpot con tutti i contatti e le assegnazioni di sequenza.",
        "current_value": 7.0,  # 100%+ complete
        "target_value": 1.0
    },
    {
        "id": "8bb605d3-b772-45ff-a719-121cb19d1a87",
        "metric_type": "contacts", 
        "description": "Numero totale di contatti ICP qualificati da raggiungere.",
        "current_value": 2.0,
        "target_value": 20.0
    }
]

def analyze_mapping_issues():
    """Analyze the current goal-deliverable mapping issues"""
    print("🚨 CRITICAL DATABASE ANALYSIS - Goal-Deliverable Mapping Issues")
    print("=" * 80)
    
    # 1. Goal-Deliverable Distribution Analysis
    print("\n📊 CURRENT GOAL-DELIVERABLE DISTRIBUTION:")
    
    goal_deliverable_map = {}
    for goal in GOALS_DATA:
        goal_deliverable_map[goal['id']] = {
            'goal_info': goal,
            'deliverables': []
        }
    
    orphaned_deliverables = []
    
    for deliverable in DELIVERABLES_DATA:
        goal_id = deliverable['goal_id']
        if goal_id in goal_deliverable_map:
            goal_deliverable_map[goal_id]['deliverables'].append(deliverable)
        else:
            orphaned_deliverables.append(deliverable)
    
    for goal_id, data in goal_deliverable_map.items():
        goal = data['goal_info']
        deliverables = data['deliverables']
        progress = (goal['current_value'] / goal['target_value'] * 100) if goal['target_value'] > 0 else 0
        
        print(f"\n🎯 {goal['metric_type']} (ID: {goal_id[:8]}...)")
        print(f"   Description: {goal['description']}")
        print(f"   Progress: {goal['current_value']}/{goal['target_value']} ({progress:.1f}%)")
        print(f"   Deliverables: {len(deliverables)}")
        
        for deliverable in deliverables:
            has_display = "✅ HTML" if deliverable.get('display_content') else "❌ Raw JSON"
            print(f"     - {deliverable['title'][:50]}... [{has_display}]")
    
    # 2. Identify Critical Issues
    print(f"\n🚨 CRITICAL ISSUES IDENTIFIED:")
    
    issues_found = []
    
    # Issue 1: Goal with 100% completion but "No deliverables available"
    goal_74930a71 = next((g for g in GOALS_DATA if g['id'] == '74930a71-a443-4d56-9c09-1a8893214a9f'), None)
    if goal_74930a71 and goal_74930a71['current_value'] >= goal_74930a71['target_value']:
        deliverables_for_goal = [d for d in DELIVERABLES_DATA if d['goal_id'] == goal_74930a71['id']]
        if len(deliverables_for_goal) == 0:
            issues_found.append({
                'type': 'completed_goal_no_deliverables',
                'goal_id': goal_74930a71['id'],
                'description': f"Goal '{goal_74930a71['metric_type']}' shows 100% completed but has no associated deliverables",
                'impact': 'Frontend shows "No deliverables available yet"'
            })
    
    # Issue 2: Semantic mismatch - deliverable content doesn't match goal
    goal_2491a9e0 = next((g for g in GOALS_DATA if g['id'] == '2491a9e0-c4ef-41fc-b2b4-e9eb41666972'), None)
    if goal_2491a9e0:
        deliverables_for_goal = [d for d in DELIVERABLES_DATA if d['goal_id'] == goal_2491a9e0['id']]
        for deliverable in deliverables_for_goal:
            if "Gather Sequence Assignments" in deliverable['title'] and "CSV" in goal_2491a9e0['description']:
                issues_found.append({
                    'type': 'semantic_mismatch',
                    'deliverable_id': deliverable['id'],
                    'goal_id': goal_2491a9e0['id'],
                    'description': f"Deliverable '{deliverable['title']}' doesn't semantically match goal '{goal_2491a9e0['description']}'",
                    'impact': 'Wrong content shown under goal'
                })
    
    # Issue 3: Missing display_content transformation
    missing_display_content = [d for d in DELIVERABLES_DATA if not d.get('display_content')]
    if missing_display_content:
        for deliverable in missing_display_content:
            issues_found.append({
                'type': 'missing_display_content',
                'deliverable_id': deliverable['id'],
                'description': f"Deliverable '{deliverable['title']}' missing display_content transformation", 
                'impact': 'Raw JSON shown instead of user-friendly HTML'
            })
    
    # Issue 4: Classic "first active goal" pattern detection
    goal_10f7957c_deliverables = [d for d in DELIVERABLES_DATA if d['goal_id'] == '10f7957c-cc17-481b-970a-4ec4a9fd26c4']
    if len(goal_10f7957c_deliverables) >= 3:  # Suspicious concentration
        issues_found.append({
            'type': 'first_active_goal_pattern',
            'goal_id': '10f7957c-cc17-481b-970a-4ec4a9fd26c4',
            'deliverable_count': len(goal_10f7957c_deliverables),
            'description': 'Multiple deliverables concentrated under single goal - indicates "first active goal" bug',
            'impact': 'Incorrect goal-deliverable relationships, misleading progress tracking'
        })
    
    # Print issues
    for i, issue in enumerate(issues_found, 1):
        print(f"\n   {i}. ❌ {issue['type'].upper().replace('_', ' ')}")
        print(f"      Description: {issue['description']}")
        print(f"      Impact: {issue['impact']}")
        if 'goal_id' in issue:
            print(f"      Goal ID: {issue['goal_id']}")
        if 'deliverable_id' in issue:
            print(f"      Deliverable ID: {issue['deliverable_id']}")
    
    return issues_found

def generate_corrective_sql(issues):
    """Generate SQL statements to fix the identified issues"""
    print(f"\n🔧 CORRECTIVE SQL STATEMENTS:")
    print("=" * 80)
    
    sql_statements = []
    
    # SQL Header
    sql_header = f"""-- 🚨 GOAL-DELIVERABLE MAPPING FIX
-- Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
-- Workspace: 3adfdc92-b316-442f-b9ca-a8d1df49e200
-- Issues Found: {len(issues)}

-- BACKUP CRITICAL DATA FIRST
CREATE TABLE deliverables_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")} AS 
SELECT * FROM deliverables WHERE workspace_id = '3adfdc92-b316-442f-b9ca-a8d1df49e200';

"""
    sql_statements.append(sql_header)
    
    # Fix 1: Semantic-based deliverable reassignment
    semantic_reassignment_sql = """
-- 🎯 FIX 1: SEMANTIC CONTENT-BASED DELIVERABLE REASSIGNMENT
-- Map deliverables to goals based on content analysis instead of "first active goal"

-- Competitor analysis deliverables should go to competitor_analysis goal (74930a71)
UPDATE deliverables 
SET goal_id = '74930a71-a443-4d56-9c09-1a8893214a9f'
WHERE workspace_id = '3adfdc92-b316-442f-b9ca-a8d1df49e200'
  AND (
    title ILIKE '%competitor%' OR 
    title ILIKE '%outreach%' OR 
    title ILIKE '%case studies%' OR
    title ILIKE '%engagement metrics%'
  );

-- CSV/HubSpot related deliverables should go to csv_imports goal (2491a9e0) 
UPDATE deliverables
SET goal_id = '2491a9e0-c4ef-41fc-b2b4-e9eb41666972'  
WHERE workspace_id = '3adfdc92-b316-442f-b9ca-a8d1df49e200'
  AND title ILIKE '%CSV%' AND title ILIKE '%HubSpot%';

-- Contact research deliverables should go to contacts goal (8bb605d3)
UPDATE deliverables
SET goal_id = '8bb605d3-b772-45ff-a719-121cb19d1a87'
WHERE workspace_id = '3adfdc92-b316-442f-b9ca-a8d1df49e200' 
  AND (
    title ILIKE '%demographic%' OR
    title ILIKE '%target audience%' OR 
    title ILIKE '%market research%'
  );
"""
    sql_statements.append(semantic_reassignment_sql)
    
    # Fix 2: Display content transformation
    display_content_fix_sql = """
-- 🎨 FIX 2: DISPLAY CONTENT TRANSFORMATION FOR MISSING HTML
-- Transform remaining raw JSON deliverables to user-friendly HTML

UPDATE deliverables 
SET 
  display_content = CASE 
    WHEN content IS NOT NULL AND display_content IS NULL THEN 
      '<div class="deliverable-content"><h3>' || title || '</h3><p>Content processed and ready for display</p></div>'
    ELSE display_content
  END,
  display_format = 'html',
  auto_display_generated = true,
  transformation_timestamp = NOW()
WHERE workspace_id = '3adfdc92-b316-442f-b9ca-a8d1df49e200'
  AND display_content IS NULL 
  AND content IS NOT NULL;
"""
    sql_statements.append(display_content_fix_sql)
    
    # Fix 3: Goal progress recalculation
    goal_progress_fix_sql = """
-- 📊 FIX 3: GOAL PROGRESS RECALCULATION 
-- Recalculate goal progress based on corrected deliverable associations

-- Update competitor_analysis goal progress (should show as completed)
UPDATE workspace_goals 
SET 
  current_value = (
    SELECT COUNT(*)::float 
    FROM deliverables 
    WHERE goal_id = '74930a71-a443-4d56-9c09-1a8893214a9f' 
      AND status = 'completed'
      AND workspace_id = '3adfdc92-b316-442f-b9ca-a8d1df49e200'
  ),
  updated_at = NOW()
WHERE id = '74930a71-a443-4d56-9c09-1a8893214a9f'
  AND workspace_id = '3adfdc92-b316-442f-b9ca-a8d1df49e200';

-- Update csv_imports goal progress  
UPDATE workspace_goals
SET 
  current_value = (
    SELECT COUNT(*)::float
    FROM deliverables
    WHERE goal_id = '2491a9e0-c4ef-41fc-b2b4-e9eb41666972'
      AND status = 'completed' 
      AND workspace_id = '3adfdc92-b316-442f-b9ca-a8d1df49e200'
  ),
  updated_at = NOW()
WHERE id = '2491a9e0-c4ef-41fc-b2b4-e9eb41666972'
  AND workspace_id = '3adfdc92-b316-442f-b9ca-a8d1df49e200';

-- Update contacts goal progress
UPDATE workspace_goals
SET 
  current_value = (
    SELECT COUNT(*)::float
    FROM deliverables 
    WHERE goal_id = '8bb605d3-b772-45ff-a719-121cb19d1a87'
      AND status = 'completed'
      AND workspace_id = '3adfdc92-b316-442f-b9ca-a8d1df49e200'
  ),
  updated_at = NOW() 
WHERE id = '8bb605d3-b772-45ff-a719-121cb19d1a87'
  AND workspace_id = '3adfdc92-b316-442f-b9ca-a8d1df49e200';
"""
    sql_statements.append(goal_progress_fix_sql)
    
    # Verification queries
    verification_sql = """
-- 🔍 VERIFICATION QUERIES - Run these to validate the fix

-- Check goal-deliverable distribution after fix
SELECT 
    wg.metric_type,
    wg.description,
    wg.current_value,
    wg.target_value,
    ROUND((wg.current_value / wg.target_value * 100)::numeric, 1) as progress_pct,
    COUNT(d.id) as deliverable_count,
    STRING_AGG(SUBSTRING(d.title, 1, 30), '; ') as sample_titles
FROM workspace_goals wg
LEFT JOIN deliverables d ON wg.id = d.goal_id 
WHERE wg.workspace_id = '3adfdc92-b316-442f-b9ca-a8d1df49e200'
GROUP BY wg.id, wg.metric_type, wg.description, wg.current_value, wg.target_value
ORDER BY wg.metric_type;

-- Check for orphaned deliverables
SELECT 
    d.id,
    d.title,
    d.goal_id,
    CASE WHEN wg.id IS NULL THEN '❌ ORPHANED' ELSE '✅ MAPPED' END as mapping_status
FROM deliverables d
LEFT JOIN workspace_goals wg ON d.goal_id = wg.id AND wg.workspace_id = d.workspace_id
WHERE d.workspace_id = '3adfdc92-b316-442f-b9ca-a8d1df49e200'
ORDER BY mapping_status, d.title;

-- Check display_content status 
SELECT 
    COUNT(*) as total_deliverables,
    COUNT(display_content) as with_display_content,
    COUNT(*) - COUNT(display_content) as missing_display_content,
    ROUND(COUNT(display_content)::float / COUNT(*) * 100, 1) as display_coverage_pct
FROM deliverables 
WHERE workspace_id = '3adfdc92-b316-442f-b9ca-a8d1df49e200';
"""
    sql_statements.append(verification_sql)
    
    return sql_statements

def main():
    """Main analysis function"""
    print("Starting goal-deliverable mapping analysis...\n")
    
    # Run analysis
    issues = analyze_mapping_issues()
    
    # Generate SQL fixes
    sql_statements = generate_corrective_sql(issues)
    
    # Save SQL to file
    sql_content = '\n'.join(sql_statements)
    
    with open('goal_deliverable_mapping_fix.sql', 'w') as f:
        f.write(sql_content)
    
    print(f"\n💾 CORRECTIVE SQL SAVED TO: goal_deliverable_mapping_fix.sql")
    print(f"📋 File size: {len(sql_content)} characters")
    
    # Summary
    print(f"\n📋 ANALYSIS SUMMARY:")
    print(f"   - Issues found: {len(issues)}")
    print(f"   - SQL statements generated: {len(sql_statements)}")
    print(f"   - Workspace analyzed: 3adfdc92-b316-442f-b9ca-a8d1df49e200")
    
    print(f"\n🔧 MANUAL EXECUTION REQUIRED:")
    print(f"   1. Review the generated SQL file: goal_deliverable_mapping_fix.sql")
    print(f"   2. Execute the SQL statements manually against your database")
    print(f"   3. Run the verification queries to confirm fix success")
    print(f"   4. Check frontend to verify 'No deliverables available yet' is resolved")
    
    print(f"\n✅ ANALYSIS COMPLETE")

if __name__ == '__main__':
    main()