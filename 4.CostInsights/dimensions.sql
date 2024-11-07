WITH dataset AS (
    SELECT
        ARRAY['ChargeType', 'UsageAccount', 'Service', 'Region', 'UsageType', 'ResourceId', 'InstanceType', 'InstanceFamily', 'DatabaseEngine', 'Project', 'UsageCategory', 'ChargeCategory'] as d
)
SELECT Dimension FROM dataset
CROSS JOIN UNNEST(d) as t(Dimension)