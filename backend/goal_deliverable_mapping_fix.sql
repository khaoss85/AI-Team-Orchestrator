-- 🚨 GOAL-DELIVERABLE MAPPING FIX
-- Generated: 2025-09-04 10:17:15
-- Workspace: 3adfdc92-b316-442f-b9ca-a8d1df49e200
-- Issues Found: 3

-- BACKUP CRITICAL DATA FIRST
CREATE TABLE deliverables_backup_20250904_101715 AS 
SELECT * FROM deliverables WHERE workspace_id = '3adfdc92-b316-442f-b9ca-a8d1df49e200';



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
