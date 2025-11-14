-- PostgreSQL Timezone Fix for Kirana Store
-- Run these commands when connecting to PostgreSQL directly to see correct IST times

-- Set your session timezone to IST
SET timezone = 'Asia/Kolkata';

-- Now all timestamp displays in this session will be in IST
-- Check current timezone
SELECT current_setting('timezone') as current_timezone;

-- View sales with correct IST times
SELECT
    id,
    sale_date,
    sale_date::text as sale_date_ist,
    customer_name,
    total_amount
FROM sales
ORDER BY id DESC
LIMIT 10;

-- View purchases with correct IST times
SELECT
    id,
    purchase_date,
    purchase_date::text as purchase_date_ist,
    product_id,
    total_cost
FROM purchases
ORDER BY id DESC
LIMIT 10;

-- To make this permanent for your connection, you can:
-- 1. Add this to your PostgreSQL connection string: ?timezone=Asia/Kolkata
-- 2. Or run: ALTER USER your_username SET timezone = 'Asia/Kolkata';
-- 3. Or set it in your database client settings

-- Check what timezone your application is using
SHOW timezone;
