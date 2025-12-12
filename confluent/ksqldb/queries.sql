-- ============================================
-- ksqlDB 实时流处理查询
-- ============================================

-- 1. 创建订单流表
CREATE STREAM orders_stream (
    order_id VARCHAR,
    customer_id VARCHAR,
    timestamp BIGINT,
    delivery_address STRUCT<
        street VARCHAR,
        city VARCHAR,
        state VARCHAR,
        zip_code VARCHAR,
        latitude DOUBLE,
        longitude DOUBLE
    >,
    items ARRAY<STRUCT<
        product_id VARCHAR,
        quantity INT,
        weight_kg DOUBLE,
        dimensions STRUCT<
            length_cm DOUBLE,
            width_cm DOUBLE,
            height_cm DOUBLE
        >
    >>,
    priority VARCHAR,
    preferred_delivery_time BIGINT
) WITH (
    KAFKA_TOPIC='orders',
    VALUE_FORMAT='JSON',
    TIMESTAMP='timestamp'
);

-- 2. 创建库存更新流表
CREATE STREAM inventory_updates_stream (
    warehouse_id VARCHAR,
    warehouse_name VARCHAR,
    product_id VARCHAR,
    timestamp BIGINT,
    update_type VARCHAR,
    quantity_change INT,
    current_stock INT,
    reserved_stock INT,
    available_stock INT
) WITH (
    KAFKA_TOPIC='inventory_updates',
    VALUE_FORMAT='JSON',
    TIMESTAMP='timestamp'
);

-- 3. 创建车辆位置流表
CREATE STREAM vehicle_locations_stream (
    vehicle_id VARCHAR,
    driver_id VARCHAR,
    timestamp BIGINT,
    latitude DOUBLE,
    longitude DOUBLE,
    speed_kmh DOUBLE,
    heading DOUBLE,
    status VARCHAR,
    current_capacity INT,
    max_capacity INT,
    fuel_level DOUBLE
) WITH (
    KAFKA_TOPIC='vehicle_locations',
    VALUE_FORMAT='JSON',
    TIMESTAMP='timestamp'
);

-- 4. 创建交通数据流表
CREATE STREAM traffic_updates_stream (
    route_id VARCHAR,
    segment_id VARCHAR,
    timestamp BIGINT,
    latitude DOUBLE,
    longitude DOUBLE,
    traffic_level VARCHAR,
    speed_kmh DOUBLE,
    congestion_percentage DOUBLE
) WITH (
    KAFKA_TOPIC='traffic_updates',
    VALUE_FORMAT='JSON',
    TIMESTAMP='timestamp'
);

-- 5. 创建天气数据流表
CREATE STREAM weather_data_stream (
    location_id VARCHAR,
    city VARCHAR,
    timestamp BIGINT,
    temperature_celsius DOUBLE,
    humidity_percentage DOUBLE,
    wind_speed_kmh DOUBLE,
    precipitation_mm DOUBLE,
    weather_condition VARCHAR
) WITH (
    KAFKA_TOPIC='weather_data',
    VALUE_FORMAT='JSON',
    TIMESTAMP='timestamp'
);

-- ============================================
-- 实时聚合查询
-- ============================================

-- 6. 各仓库实时库存水位（按商品聚合）
CREATE TABLE warehouse_inventory_levels AS
SELECT
    warehouse_id,
    warehouse_name,
    product_id,
    LATEST_BY_OFFSET(current_stock) AS current_stock,
    LATEST_BY_OFFSET(available_stock) AS available_stock,
    LATEST_BY_OFFSET(reserved_stock) AS reserved_stock,
    SUM(quantity_change) AS total_change,
    COUNT(*) AS update_count
FROM inventory_updates_stream
GROUP BY warehouse_id, warehouse_name, product_id;

-- 7. 各区域订单密度热力图（按城市和时间窗口）
CREATE TABLE order_density_heatmap AS
SELECT
    delivery_address->city AS city,
    WINDOWSTART AS window_start,
    WINDOWEND AS window_end,
    COUNT(*) AS order_count,
    SUM(ARRAY_SIZE(items)) AS total_items,
    COLLECT_LIST(order_id) AS order_ids
FROM orders_stream
WINDOW TUMBLING (SIZE 1 HOUR)
GROUP BY delivery_address->city;

-- 8. 车辆利用率指标（按车辆聚合）
CREATE TABLE vehicle_utilization AS
SELECT
    vehicle_id,
    driver_id,
    LATEST_BY_OFFSET(status) AS current_status,
    LATEST_BY_OFFSET(latitude) AS current_latitude,
    LATEST_BY_OFFSET(longitude) AS current_longitude,
    LATEST_BY_OFFSET(speed_kmh) AS current_speed,
    LATEST_BY_OFFSET(current_capacity) AS current_capacity,
    LATEST_BY_OFFSET(max_capacity) AS max_capacity,
    ROUND((LATEST_BY_OFFSET(current_capacity) * 100.0 / LATEST_BY_OFFSET(max_capacity)), 2) AS utilization_percentage,
    LATEST_BY_OFFSET(fuel_level) AS fuel_level,
    COUNT(*) AS location_updates
FROM vehicle_locations_stream
GROUP BY vehicle_id, driver_id;

-- 9. 按优先级统计订单（实时）
CREATE TABLE orders_by_priority AS
SELECT
    priority,
    COUNT(*) AS order_count,
    SUM(ARRAY_SIZE(items)) AS total_items,
    COLLECT_LIST(order_id) AS order_ids
FROM orders_stream
GROUP BY priority;

-- ============================================
-- 流-流关联查询
-- ============================================

-- 10. 订单与库存关联（检查库存可用性）
CREATE STREAM orders_with_inventory_check AS
SELECT
    o.order_id,
    o.customer_id,
    o.delivery_address,
    o.items,
    o.priority,
    i.warehouse_id,
    i.available_stock,
    CASE
        WHEN i.available_stock >= ARRAY_SIZE(o.items) THEN 'IN_STOCK'
        ELSE 'LOW_STOCK'
    END AS stock_status
FROM orders_stream o
INNER JOIN warehouse_inventory_levels i
    ON o.items[0]->product_id = i.product_id
    AND o.delivery_address->city = i.warehouse_name;

-- 11. 车辆与交通关联（实时ETA计算）
CREATE STREAM vehicles_with_traffic AS
SELECT
    v.vehicle_id,
    v.driver_id,
    v.latitude AS vehicle_lat,
    v.longitude AS vehicle_lon,
    v.status,
    v.speed_kmh AS vehicle_speed,
    t.traffic_level,
    t.speed_kmh AS traffic_speed,
    t.congestion_percentage,
    CASE
        WHEN t.congestion_percentage > 70 THEN 'HEAVY_CONGESTION'
        WHEN t.congestion_percentage > 40 THEN 'MODERATE_CONGESTION'
        ELSE 'LIGHT_CONGESTION'
    END AS congestion_status
FROM vehicle_locations_stream v
INNER JOIN traffic_updates_stream t
    WITHIN 5 MINUTES
    ON ABS(v.latitude - t.latitude) < 0.01
    AND ABS(v.longitude - t.longitude) < 0.01;

-- ============================================
-- 数据富化查询
-- ============================================

-- 12. 订单数据富化（添加地理区域和时间特征）
CREATE STREAM enriched_orders AS
SELECT
    order_id,
    customer_id,
    timestamp,
    delivery_address,
    delivery_address->city AS city,
    delivery_address->latitude AS latitude,
    delivery_address->longitude AS longitude,
    -- 计算配送区域（简化：基于坐标）
    CASE
        WHEN delivery_address->latitude > 35 THEN 'NORTH'
        WHEN delivery_address->latitude < 25 THEN 'SOUTH'
        ELSE 'CENTRAL'
    END AS region,
    items,
    ARRAY_SIZE(items) AS item_count,
    priority,
    preferred_delivery_time,
    -- 计算时间特征
    EXTRACT(DAY_OF_WEEK FROM TIMESTAMPTOSTRING(timestamp, 'yyyy-MM-dd HH:mm:ss')) AS day_of_week,
    EXTRACT(HOUR FROM TIMESTAMPTOSTRING(timestamp, 'yyyy-MM-dd HH:mm:ss')) AS hour_of_day,
    -- 计算期望配送时长（毫秒）
    preferred_delivery_time - timestamp AS expected_delivery_duration_ms
FROM orders_stream;

-- 13. 车辆位置富化（添加距离和ETA估算）
CREATE STREAM enriched_vehicle_locations AS
SELECT
    vehicle_id,
    driver_id,
    timestamp,
    latitude,
    longitude,
    speed_kmh,
    heading,
    status,
    current_capacity,
    max_capacity,
    fuel_level,
    -- 计算利用率
    ROUND((current_capacity * 100.0 / max_capacity), 2) AS utilization_percentage,
    -- 估算剩余配送时间（基于当前速度和容量）
    CASE
        WHEN status = 'DELIVERING' AND current_capacity > 0 THEN
            (current_capacity * 15 * 60 * 1000)  -- 假设每个包裹15分钟
        ELSE 0
    END AS estimated_remaining_time_ms
FROM vehicle_locations_stream;

-- ============================================
-- 异常检测查询
-- ============================================

-- 14. 异常订单检测（超大订单、异常地址等）
CREATE STREAM anomaly_orders AS
SELECT
    order_id,
    customer_id,
    delivery_address,
    items,
    ARRAY_SIZE(items) AS item_count,
    priority,
    'LARGE_ORDER' AS anomaly_type,
    '订单商品数量异常' AS anomaly_description
FROM orders_stream
WHERE ARRAY_SIZE(items) > 10
    OR priority = 'SAME_DAY' AND ARRAY_SIZE(items) > 5;

-- 15. 车辆异常状态检测
CREATE STREAM anomaly_vehicles AS
SELECT
    vehicle_id,
    driver_id,
    status,
    current_capacity,
    max_capacity,
    fuel_level,
    speed_kmh,
    'LOW_FUEL' AS anomaly_type,
    '燃油不足' AS anomaly_description
FROM vehicle_locations_stream
WHERE fuel_level < 20
    OR (status = 'IN_TRANSIT' AND speed_kmh < 10 AND fuel_level > 50)  -- 低速异常
    OR current_capacity > max_capacity;  -- 超载

