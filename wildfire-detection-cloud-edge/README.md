# Real-Time Wildfire Detection Using Edge + Cloud

A production-style reference project for real-time wildfire monitoring using **YOLOv8 at the edge** and **Azure cloud services** for ingestion, processing, and alerting.

## Architecture

```text
Camera Feed → Edge Device → Azure IoT Hub → Azure Function → Alert System (Email/SMS)
                           ↘ Azure ML (training/retraining pipeline)
```

### Edge Layer
- Captures live frames with OpenCV.
- Runs YOLOv8 inference to detect `fire/wildfire/smoke`.
- Emits events to cloud when confidence exceeds threshold (`0.6` default).
- Supports secure transport via:
  - Azure IoT Hub Device SDK (TLS)
  - HTTPS webhook fallback

### Cloud Layer (Azure)
1. **Azure IoT Hub**
   - Device authentication and telemetry intake.
2. **Azure Functions**
   - Triggered from IoT Hub routed events via Event Hub binding.
   - Sends email and optional SMS alerts.
3. **Azure Machine Learning-ready scripts**
   - Dataset YAML generation
   - YOLO training/retraining script

### Alert Message Format

```text
Wildfire detected at {timestamp}. Confidence: {score}
```

---

## Repository Structure

```text
wildfire-detection-cloud-edge/
│
├── edge/
│   ├── camera_stream.py
│   ├── yolo_inference.py
│   └── send_event_to_cloud.py
│
├── cloud/
│   ├── azure_function_alert.py
│   └── iot_hub_receiver.py
│
├── ml/
│   ├── train_model.py
│   └── dataset_loader.py
│
├── docker/
│   └── Dockerfile
│
├── requirements.txt
└── README.md
```

---

## Setup

### 1) Create environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Environment variables

Set only what you need based on components you run.

#### Edge (IoT transport)

```bash
export EDGE_CLOUD_TRANSPORT=iot
export IOTHUB_DEVICE_CONNECTION_STRING="<device-connection-string>"
export EDGE_DEVICE_ID="edge-cam-001"
export FIRE_CONFIDENCE_THRESHOLD="0.6"
export YOLO_MODEL_PATH="yolov8n.pt"
```

#### Edge (HTTP fallback)

```bash
export EDGE_CLOUD_TRANSPORT=http
export ALERT_WEBHOOK_URL="https://<secure-endpoint>/wildfire"
```

#### Cloud alerts

```bash
export SENDGRID_API_KEY="<sendgrid-key>"
export ALERT_EMAIL_FROM="noreply@example.com"
export ALERT_EMAIL_TO="ops@example.com"

# Optional SMS
export TWILIO_ACCOUNT_SID="<sid>"
export TWILIO_AUTH_TOKEN="<token>"
export TWILIO_FROM_NUMBER="+10000000000"
export TWILIO_TO_NUMBER="+10000000001"
```

#### IoT Hub telemetry receiver utility

```bash
export IOTHUB_EVENTHUB_CONNECTION_STRING="<eventhub-compatible-connection-string>"
export EVENTHUB_CONSUMER_GROUP="$Default"
```

---

## Run Locally

### Edge real-time inference

```bash
cd edge
python camera_stream.py
```

### IoT Hub receiver utility (cloud monitoring)

```bash
cd cloud
python iot_hub_receiver.py
```

### Train YOLO model

```bash
cd ml
python dataset_loader.py --dataset-root /path/to/wildfire-dataset --output data/wildfire.yaml --classes "0:fire,1:smoke"
python train_model.py --data data/wildfire.yaml --model yolov8n.pt --epochs 50 --imgsz 640 --batch 8
```

---

## Azure Deployment Guidance

### Azure IoT Hub
1. Create IoT Hub and register edge device.
2. Copy device connection string into `IOTHUB_DEVICE_CONNECTION_STRING`.
3. Configure message routing from IoT Hub to Event Hub-compatible endpoint for Functions.

### Azure Function
1. Create Python Azure Function App.
2. Add an Event Hub trigger bound to IoT Hub route.
3. Use `cloud/azure_function_alert.py` logic as your function entry-point.
4. Configure app settings for SendGrid/Twilio secrets (prefer Azure Key Vault references).

### Azure ML
1. Upload dataset to Azure ML datastore.
2. Run `ml/dataset_loader.py` and `ml/train_model.py` in Azure ML jobs.
3. Register best model artifact (`best.pt`) and deploy updated model to edge fleet.

---

## Docker

Build image from project root:

```bash
docker build -f docker/Dockerfile -t wildfire-edge:latest .
```

Run container:

```bash
docker run --rm -it \
  --device=/dev/video0:/dev/video0 \
  -e EDGE_CLOUD_TRANSPORT=iot \
  -e IOTHUB_DEVICE_CONNECTION_STRING="<device-connection-string>" \
  wildfire-edge:latest
```

---

## Security Notes

- IoT Hub device authentication is handled by Azure connection credentials and TLS.
- Use HTTPS only for webhook fallback transport.
- Keep all API keys and connection strings in secret stores (Azure Key Vault / CI secrets), never hardcode.
- Enable IoT Hub access policies with least privilege.

## Logging and Operations

- All modules use Python logging with structured, timestamped output.
- Increase verbosity by setting Python logging level as needed.
- Consider shipping edge/cloud logs to Azure Monitor in production.
