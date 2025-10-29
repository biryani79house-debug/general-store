-- Fix created_by field for existing purchase records in PostgreSQL database
-- This script sets a default admin user for purchases that have NULL created_by

-- Step 1: Check how many purchase records have NULL created_by
SELECT COUNT(*) as null_created_by_count FROM purchases WHERE created_by IS NULL;

-- Step 2: Find the admin user ID (assuming admin username is 'raza123')
-- If 'raza123' doesn't exist, use any active user as fallback
SELECT id, username FROM users WHERE username = 'raza123' AND is_active = true;

-- If the above returns no rows, use this as fallback:
-- SELECT id, username FROM users WHERE is_active = true LIMIT 1;

-- Step 3: Update all purchase records with NULL created_by
-- Replace ? with the actual admin user ID from step 2
UPDATE purchases
SET created_by = (
    SELECT id FROM users
    WHERE username = 'raza123'
    AND is_active = true
    LIMIT 1
)
WHERE created_by IS NULL;

-- If the above doesn't work (no admin user with 'raza123'), use this fallback:
-- UPDATE purchases
-- SET created_by = (
--     SELECT id FROM users
--     WHERE is_active = true
--     LIMIT 1
-- )
-- WHERE created_by IS NULL;

-- Step 4: Verify the fix worked
SELECT COUNT(*) as remaining_null_count FROM purchases WHERE created_by IS NULL;

-- Step 5: Show statistics
SELECT
    (SELECT COUNT(*) FROM purchases) as total_purchases,
    (SELECT COUNT(*) FROM purchases WHERE created_by IS NOT NULL) as non_null_created_by,
    (SELECT COUNT(*) FROM purchases WHERE created_by IS NULL) as remaining_null_created_by;

-- Optional: Show some purchase records to verify usernames
SELECT
    p.id,
    p.product_id,
    pr.name as product_name,
    p.quantity,
    p.purchase_date,
    u.username as created_by_user,
    p.created_by
FROM purchases p
LEFT JOIN products pr ON p.product_id = pr.id
LEFT JOIN users u ON p.created_by = u.id
ORDER BY p.purchase_date DESC
LIMIT 10;
