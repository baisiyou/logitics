import React, { useState, useEffect, useMemo } from 'react';
import { Box, Grid, Paper, Typography, Card, CardContent } from '@mui/material';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import axios from 'axios';
import './App.css';

// 修复Leaflet默认图标问题
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const DISPATCH_CENTER_URL = 'http://localhost:8001';

function App() {
  const [statistics, setStatistics] = useState({
    total_orders_today: 0,
    active_vehicles: 0,
    delivered_today: 0,
    pending_orders: 0
  });
  const [orders, setOrders] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [demandPredictions, setDemandPredictions] = useState([]);
  const [ws, setWs] = useState(null);

  useEffect(() => {
    // 连接WebSocket
    const websocket = new WebSocket(`ws://localhost:8001/ws`);
    
    websocket.onopen = () => {
      console.log('WebSocket连接已建立');
      setWs(websocket);
    };

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'initial_state') {
        setStatistics(data.data.statistics || statistics);
        setOrders(Object.values(data.data.orders || {}));
        setVehicles(Object.values(data.data.vehicles || {}));
        setAlerts(data.data.alerts || []);
        setDemandPredictions(Object.values(data.data.demand_predictions || {}));
      } else if (data.type === 'order_assigned') {
        // 更新订单状态 - 通过重新获取数据来更新
        // 数据会通过定期轮询自动更新
      } else if (data.type === 'alert') {
        setAlerts(prev => [data.data, ...prev].slice(0, 50));
      }
    };

    websocket.onerror = (error) => {
      console.error('WebSocket错误:', error);
    };

    websocket.onclose = () => {
      console.log('WebSocket连接已关闭');
    };

    // 定期获取数据
    const fetchData = async () => {
      try {
        const [statsRes, ordersRes, vehiclesRes, alertsRes, predictionsRes] = await Promise.all([
          axios.get(`${DISPATCH_CENTER_URL}/api/v1/statistics`),
          axios.get(`${DISPATCH_CENTER_URL}/api/v1/orders`),
          axios.get(`${DISPATCH_CENTER_URL}/api/v1/vehicles`),
          axios.get(`${DISPATCH_CENTER_URL}/api/v1/alerts?limit=10`),
          axios.get(`${DISPATCH_CENTER_URL}/api/v1/demand-predictions`)
        ]);

        setStatistics(statsRes.data);
        setOrders(ordersRes.data);
        setVehicles(vehiclesRes.data);
        setAlerts(alertsRes.data);
        setDemandPredictions(predictionsRes.data);
      } catch (error) {
        console.error('获取数据失败:', error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000); // 每5秒更新

    return () => {
      websocket.close();
      clearInterval(interval);
    };
  }, []);

  // 准备图表数据 - 按时间分组统计订单数量
  const orderTrendData = useMemo(() => {
    if (!orders || !Array.isArray(orders) || orders.length === 0) {
      // 返回空数据时的占位数据
      return [{ time: '00:00', orders: 0 }];
    }
    
    // 按小时分组统计
    const hourlyData = {};
    const now = Date.now();
    const hoursToShow = 12; // 显示最近12小时
    
    // 初始化12小时的数据点
    for (let i = hoursToShow - 1; i >= 0; i--) {
      const hourTimestamp = now - (i * 60 * 60 * 1000);
      const hourKey = new Date(hourTimestamp).toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false 
      });
      hourlyData[hourKey] = 0;
    }
    
    // 统计每个小时的订单数
    orders.forEach(order => {
      if (order && order.timestamp) {
        try {
          const orderDate = new Date(order.timestamp);
          const hourKey = orderDate.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: false 
          });
          
          if (hourlyData.hasOwnProperty(hourKey)) {
            hourlyData[hourKey]++;
          } else {
            // 如果不在12小时内，添加到最近的小时
            const keys = Object.keys(hourlyData);
            if (keys.length > 0) {
              hourlyData[keys[keys.length - 1]]++;
            }
          }
        } catch (e) {
          console.error('Error processing order timestamp:', e);
        }
      }
    });
    
    // 转换为图表数据格式，确保至少有一些数据
    const chartData = Object.entries(hourlyData).map(([time, count]) => ({
      time: time,
      orders: count
    }));
    
    return chartData.length > 0 ? chartData : [{ time: '00:00', orders: 0 }];
  }, [orders]);

  const vehicleStatusData = [
    { status: 'Idle', count: vehicles.filter(v => v.status === 'IDLE').length },
    { status: 'Loading', count: vehicles.filter(v => v.status === 'LOADING').length },
    { status: 'In Transit', count: vehicles.filter(v => v.status === 'IN_TRANSIT').length },
    { status: 'Delivering', count: vehicles.filter(v => v.status === 'DELIVERING').length },
  ];

  return (
    <Box sx={{ flexGrow: 1, p: 3, backgroundColor: '#f5f5f5', minHeight: '100vh' }}>
      <Typography variant="h4" component="h1" gutterBottom sx={{ mb: 3, fontWeight: 'bold' }}>
        Amazon Logistics Network Real-Time Intelligent Dispatch System
      </Typography>

      {/* 统计卡片 */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Orders Today
              </Typography>
              <Typography variant="h4">
                {statistics.total_orders_today}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Active Vehicles
              </Typography>
              <Typography variant="h4">
                {statistics.active_vehicles}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Delivered Today
              </Typography>
              <Typography variant="h4">
                {statistics.delivered_today}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Pending Orders
              </Typography>
              <Typography variant="h4" color="error">
                {statistics.pending_orders}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 图表和地图 */}
      <Grid container spacing={3}>
        {/* 订单趋势 */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Order Trends
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={orderTrendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="orders" stroke="#8884d8" />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* 车辆状态分布 */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Vehicle Status Distribution
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={vehicleStatusData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="status" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#82ca9d" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* 地图 */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              Real-Time Vehicle Locations
            </Typography>
            <MapContainer
              center={[45.5017, -73.5673]}
              zoom={10}
              style={{ height: '350px', width: '100%' }}
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              />
              {vehicles.map((vehicle) => (
                vehicle.latitude && vehicle.longitude && (
                  <Marker
                    key={vehicle.vehicle_id}
                    position={[vehicle.latitude, vehicle.longitude]}
                  >
                    <Popup>
                      <div>
                        <strong>Vehicle ID:</strong> {vehicle.vehicle_id}<br />
                        <strong>Status:</strong> {vehicle.status}<br />
                        <strong>Speed:</strong> {vehicle.speed_kmh?.toFixed(1)} km/h<br />
                        <strong>Capacity:</strong> {vehicle.current_capacity}/{vehicle.max_capacity}
                      </div>
                    </Popup>
                  </Marker>
                )
              ))}
            </MapContainer>
          </Paper>
        </Grid>

        {/* 告警列表 */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: 400, overflow: 'auto' }}>
            <Typography variant="h6" gutterBottom>
              Real-Time Alerts
            </Typography>
            {alerts.length === 0 ? (
              <Typography color="textSecondary">No Alerts</Typography>
            ) : (
              alerts.map((alert, index) => (
                <Card key={index} sx={{ mb: 1, bgcolor: alert.severity === 'CRITICAL' ? '#ffebee' : '#fff3e0' }}>
                  <CardContent>
                    <Typography variant="subtitle2" color="error">
                      {alert.severity}
                    </Typography>
                    <Typography variant="body2">
                      {alert.data?.description || alert.data?.anomaly_type || 'Unknown Alert'}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      {new Date(alert.timestamp).toLocaleString()}
                    </Typography>
                  </CardContent>
                </Card>
              ))
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default App;

