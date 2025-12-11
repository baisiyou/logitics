-- ============================================
-- BigQuery ML Real-Time Query Analysis
-- ============================================

-- 1. Create demand prediction model (linear regression)
CREATE OR REPLACE MODEL `logistics_analytics.demand_prediction_model`
OPTIONS(
  model_type='linear_reg',
  input_label_cols=['order_count'],
  data_split_method='random',
  data_split_eval_fraction=0.2
) AS
SELECT
  city,
  region,
  EXTRACT(HOUR FROM TIMESTAMP_MILLIS(timestamp)) AS hour_of_day,
  EXTRACT(DAYOFWEEK FROM TIMESTAMP_MILLIS(timestamp)) AS day_of_week,
  EXTRACT(DAY FROM TIMESTAMP_MILLIS(timestamp)) AS day_of_month,
  CASE 
    WHEN EXTRACT(DAYOFWEEK FROM TIMESTAMP_MILLIS(timestamp)) IN (6, 7) THEN 1 
    ELSE 0 
  END AS is_weekend,
  CASE 
    WHEN EXTRACT(HOUR FROM TIMESTAMP_MILLIS(timestamp)) BETWEEN 8 AND 10 
      OR EXTRACT(HOUR FROM TIMESTAMP_MILLIS(timestamp)) BETWEEN 17 AND 19 
    THEN 1 
    ELSE 0 
  END AS is_peak_hour,
  COUNT(*) AS order_count
FROM `logistics_analytics.orders_stream`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY 
  city, 
  region, 
  EXTRACT(HOUR FROM TIMESTAMP_MILLIS(timestamp)),
  EXTRACT(DAYOFWEEK FROM TIMESTAMP_MILLIS(timestamp)),
  EXTRACT(DAY FROM TIMESTAMP_MILLIS(timestamp)),
  timestamp
HAVING COUNT(*) > 0;

-- 2. Evaluate model
SELECT
  *
FROM ML.EVALUATE(MODEL `logistics_analytics.demand_prediction_model`);

-- 3. Predict demand for next 2 hours
SELECT
  city,
  region,
  hour_of_day,
  day_of_week,
  is_weekend,
  is_peak_hour,
  predicted_order_count,
  prediction_interval_lower_bound,
  prediction_interval_upper_bound
FROM ML.PREDICT(
  MODEL `logistics_analytics.demand_prediction_model`,
  (
    SELECT
      'Montreal' AS city,
      'NORTH' AS region,
      EXTRACT(HOUR FROM CURRENT_TIMESTAMP()) AS hour_of_day,
      EXTRACT(DAYOFWEEK FROM CURRENT_TIMESTAMP()) AS day_of_week,
      CASE WHEN EXTRACT(DAYOFWEEK FROM CURRENT_TIMESTAMP()) IN (6, 7) THEN 1 ELSE 0 END AS is_weekend,
      CASE 
        WHEN EXTRACT(HOUR FROM CURRENT_TIMESTAMP()) BETWEEN 8 AND 10 
          OR EXTRACT(HOUR FROM CURRENT_TIMESTAMP()) BETWEEN 17 AND 19 
        THEN 1 
        ELSE 0 
      END AS is_peak_hour
    UNION ALL
    SELECT
      'Toronto' AS city,
      'CENTRAL' AS region,
      EXTRACT(HOUR FROM CURRENT_TIMESTAMP()) AS hour_of_day,
      EXTRACT(DAYOFWEEK FROM CURRENT_TIMESTAMP()) AS day_of_week,
      CASE WHEN EXTRACT(DAYOFWEEK FROM CURRENT_TIMESTAMP()) IN (6, 7) THEN 1 ELSE 0 END AS is_weekend,
      CASE 
        WHEN EXTRACT(HOUR FROM CURRENT_TIMESTAMP()) BETWEEN 8 AND 10 
          OR EXTRACT(HOUR FROM CURRENT_TIMESTAMP()) BETWEEN 17 AND 19 
        THEN 1 
        ELSE 0 
      END AS is_peak_hour
  )
);

-- 4. Create warehouse pressure prediction model
CREATE OR REPLACE MODEL `logistics_analytics.warehouse_pressure_model`
OPTIONS(
  model_type='linear_reg',
  input_label_cols=['pressure_score'],
  data_split_method='random',
  data_split_eval_fraction=0.2
) AS
SELECT
  warehouse_id,
  current_orders,
  current_capacity,
  pending_orders,
  (current_orders / NULLIF(current_capacity, 0)) AS utilization_ratio,
  (pending_orders / NULLIF(current_capacity, 0)) AS pending_ratio,
  EXTRACT(HOUR FROM TIMESTAMP_MILLIS(timestamp)) AS hour_of_day,
  CASE 
    WHEN (current_orders / NULLIF(current_capacity, 0)) >= 0.9 THEN 0.95
    WHEN (current_orders / NULLIF(current_capacity, 0)) >= 0.7 THEN 0.8
    WHEN (current_orders / NULLIF(current_capacity, 0)) >= 0.5 THEN 0.6
    ELSE (current_orders / NULLIF(current_capacity, 0)) * 0.5
  END AS pressure_score
FROM `logistics_analytics.warehouse_status_stream`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY);

-- 5. Real-time query: current pressure for each warehouse
SELECT
  warehouse_id,
  warehouse_name,
  current_orders,
  current_capacity,
  pending_orders,
  ROUND((current_orders / NULLIF(current_capacity, 0)) * 100, 2) AS utilization_percentage,
  predicted_pressure_score,
  CASE
    WHEN predicted_pressure_score >= 0.9 THEN 'CRITICAL'
    WHEN predicted_pressure_score >= 0.7 THEN 'HIGH'
    WHEN predicted_pressure_score >= 0.5 THEN 'MEDIUM'
    ELSE 'LOW'
  END AS pressure_level
FROM ML.PREDICT(
  MODEL `logistics_analytics.warehouse_pressure_model`,
  (
    SELECT
      warehouse_id,
      warehouse_name,
      current_orders,
      current_capacity,
      pending_orders,
      (current_orders / NULLIF(current_capacity, 0)) AS utilization_ratio,
      (pending_orders / NULLIF(current_capacity, 0)) AS pending_ratio,
      EXTRACT(HOUR FROM CURRENT_TIMESTAMP()) AS hour_of_day
    FROM `logistics_analytics.warehouse_inventory_levels`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
  )
)
ORDER BY predicted_pressure_score DESC;

-- 6. Create anomaly detection model (using K-means clustering)
CREATE OR REPLACE MODEL `logistics_analytics.anomaly_detection_model`
OPTIONS(
  model_type='kmeans',
  num_clusters=5,
  kmeans_init_method='kmeans++'
) AS
SELECT
  vehicle_id,
  speed_kmh,
  fuel_level,
  (current_capacity / NULLIF(max_capacity, 0)) AS capacity_ratio,
  EXTRACT(HOUR FROM TIMESTAMP_MILLIS(timestamp)) AS hour_of_day
FROM `logistics_analytics.vehicle_locations_stream`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND speed_kmh > 0;

-- 7. Detect anomalous vehicles
WITH vehicle_features AS (
  SELECT
    vehicle_id,
    driver_id,
    speed_kmh,
    fuel_level,
    (current_capacity / NULLIF(max_capacity, 0)) AS capacity_ratio,
    EXTRACT(HOUR FROM TIMESTAMP_MILLIS(timestamp)) AS hour_of_day,
    timestamp
  FROM `logistics_analytics.vehicle_locations_stream`
  WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
),
anomaly_scores AS (
  SELECT
    vf.*,
    ML.DISTANCE(
      ML.PREDICT(MODEL `logistics_analytics.anomaly_detection_model`, (SELECT * FROM vehicle_features LIMIT 1)),
      ML.PREDICT(MODEL `logistics_analytics.anomaly_detection_model`, vf)
    ) AS distance_to_centroid
  FROM vehicle_features vf
)
SELECT
  vehicle_id,
  driver_id,
  speed_kmh,
  fuel_level,
  capacity_ratio,
  distance_to_centroid,
  CASE
    WHEN fuel_level < 15 THEN 'LOW_FUEL'
    WHEN capacity_ratio > 1.0 THEN 'OVERLOADED'
    WHEN speed_kmh < 5 AND fuel_level > 50 THEN 'LOW_SPEED_ANOMALY'
    WHEN distance_to_centroid > (
      SELECT PERCENTILE_CONT(distance_to_centroid, 0.95) 
      FROM anomaly_scores
    ) THEN 'OUTLIER'
    ELSE 'NORMAL'
  END AS anomaly_type
FROM anomaly_scores
WHERE 
  fuel_level < 15 
  OR capacity_ratio > 1.0
  OR (speed_kmh < 5 AND fuel_level > 50)
  OR distance_to_centroid > (
    SELECT PERCENTILE_CONT(distance_to_centroid, 0.95) 
    FROM anomaly_scores
  )
ORDER BY distance_to_centroid DESC;

-- 8. Real-time demand prediction query (by region)
SELECT
  city,
  region,
  hour_of_day,
  day_of_week,
  AVG(predicted_order_count) AS avg_predicted_orders,
  STDDEV(predicted_order_count) AS stddev_predicted_orders,
  MIN(prediction_interval_lower_bound) AS min_orders,
  MAX(prediction_interval_upper_bound) AS max_orders
FROM ML.PREDICT(
  MODEL `logistics_analytics.demand_prediction_model`,
  (
    SELECT DISTINCT
      city,
      region,
      EXTRACT(HOUR FROM CURRENT_TIMESTAMP()) AS hour_of_day,
      EXTRACT(DAYOFWEEK FROM CURRENT_TIMESTAMP()) AS day_of_week,
      CASE WHEN EXTRACT(DAYOFWEEK FROM CURRENT_TIMESTAMP()) IN (6, 7) THEN 1 ELSE 0 END AS is_weekend,
      CASE 
        WHEN EXTRACT(HOUR FROM CURRENT_TIMESTAMP()) BETWEEN 8 AND 10 
          OR EXTRACT(HOUR FROM CURRENT_TIMESTAMP()) BETWEEN 17 AND 19 
        THEN 1 
        ELSE 0 
      END AS is_peak_hour
    FROM `logistics_analytics.orders_stream`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
  )
)
GROUP BY city, region, hour_of_day, day_of_week
ORDER BY avg_predicted_orders DESC;

