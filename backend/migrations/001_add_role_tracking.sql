-- Migration: Add role-based cost tracking to analysis_history
-- Run this if you already have data in your database

-- Add new columns for role tracking
ALTER TABLE analysis_history 
ADD COLUMN IF NOT EXISTS assignee VARCHAR(255),
ADD COLUMN IF NOT EXISTS assignee_role VARCHAR(100),
ADD COLUMN IF NOT EXISTS total_estimated_cost FLOAT;

-- Create index for assignee lookups
CREATE INDEX IF NOT EXISTS idx_analysis_assignee ON analysis_history(assignee);
CREATE INDEX IF NOT EXISTS idx_analysis_role ON analysis_history(assignee_role);

-- Show summary
SELECT 
    'Migration complete!' as status,
    COUNT(*) as total_records,
    COUNT(assignee) as records_with_assignee,
    COUNT(assignee_role) as records_with_role
FROM analysis_history;
