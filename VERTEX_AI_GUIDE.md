# Vertex AI Integration Guide

## Overview

Yes! The system **already includes Vertex AI integration**. Vertex AI is Google Cloud's unified ML platform for building, deploying, and managing ML models.

## Current Integration

### ✅ What's Already Implemented

1. **Vertex AI Service** (`ai-inference/vertex_ai_service.py`)
   - Demand prediction model
   - Warehouse pressure prediction
   - ETA dynamic update
   - Anomaly detection

2. **Configuration**
   - GCP Project: `baisiyou`
   - Vertex AI Location: `us-central1`
   - Credentials: `config/gcp-credentials.json`

3. **API Endpoints**
   - `/api/v1/predict/demand` - Demand prediction
   - `/api/v1/predict/warehouse-pressure` - Warehouse pressure
   - `/api/v1/calculate/eta` - ETA calculation
   - `/api/v1/detect/anomaly` - Anomaly detection

## Current Implementation Status

### Working Features (Statistical Baseline)

The system currently uses **statistical baseline models** that work without training:
- ✅ Demand prediction (based on historical averages)
- ✅ Warehouse pressure prediction (based on utilization)
- ✅ ETA calculation (based on distance and traffic)
- ✅ Anomaly detection (rule-based)

### Vertex AI Endpoint Integration (Optional)

For production ML models, you can:
1. Train models in Vertex AI
2. Deploy to Vertex AI endpoints
3. Update `VERTEX_AI_ENDPOINT_ID` in `.env`
4. System will automatically use Vertex AI endpoints

## Setup and Usage

### 1. Verify Configuration

```bash
# Check GCP project
cat .env | grep GOOGLE_CLOUD_PROJECT

# Check credentials
ls -lh config/gcp-credentials.json

# Check Vertex AI location
cat .env | grep VERTEX_AI_LOCATION
```

### 2. Enable Vertex AI API

```bash
export PATH="$HOME/google-cloud-sdk/bin:$PATH"
gcloud services enable aiplatform.googleapis.com --project=baisiyou
```

### 3. Test Vertex AI Service

```bash
# Health check
curl http://localhost:8000/health

# Test demand prediction
curl -X POST http://localhost:8000/api/v1/predict/demand \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Montreal",
    "region": "NORTH",
    "hour_of_day": 14,
    "day_of_week": 1,
    "historical_orders": []
  }'
```

## Training Custom Models (Advanced)

### Step 1: Prepare Training Data

Export data from Kafka/BigQuery to train models:

```python
# Example: Export order data for training
from google.cloud import bigquery
client = bigquery.Client(project='baisiyou')
query = "SELECT * FROM logistics_analytics.orders_stream"
df = client.query(query).to_dataframe()
```

### Step 2: Train Model in Vertex AI

```python
from google.cloud import aiplatform

aiplatform.init(project='baisiyou', location='us-central1')

# Train AutoML model
dataset = aiplatform.Dataset.create(
    display_name='logistics-orders',
    gcs_source='gs://your-bucket/data.csv'
)

model = aiplatform.AutoMLForecastingTrainingJob(
    display_name='demand-prediction',
    optimization_objective='minimize-rmse'
).run(
    dataset=dataset,
    target_column='order_count',
    time_column='timestamp',
    time_series_identifier_column='city'
)
```

### Step 3: Deploy Model

```python
# Deploy to endpoint
endpoint = model.deploy(
    deployed_model_display_name='demand-prediction-v1',
    machine_type='n1-standard-2'
)

# Get endpoint ID
print(f"Endpoint ID: {endpoint.resource_name}")
```

### Step 4: Update Configuration

Add to `.env`:
```
VERTEX_AI_ENDPOINT_ID=your-endpoint-id
```

## Current Limitations

1. **No Trained Models Yet**
   - Currently using statistical baselines
   - Need to train models for production use

2. **Billing Required**
   - Vertex AI API needs billing enabled
   - Training/deployment costs apply

3. **Endpoint Not Configured**
   - `VERTEX_AI_ENDPOINT_ID` is empty
   - System falls back to statistical models

## Cost Considerations

- **API Calls**: ~$0.001-0.01 per prediction
- **Training**: ~$10-100 per model
- **Endpoint**: ~$50-200/month per endpoint
- **Free Tier**: Limited (check current limits)

## Next Steps

1. **For Testing**: Current statistical models work fine
2. **For Production**: Train and deploy Vertex AI models
3. **For Development**: Use local statistical models (free)

## Resources

- Vertex AI Documentation: https://cloud.google.com/vertex-ai/docs
- BigQuery ML: For SQL-based ML models
- AutoML: For automated model training

