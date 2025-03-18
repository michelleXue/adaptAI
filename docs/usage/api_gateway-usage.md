# API Gateway

## Introduction
The API Gateway acts as the central entry point for handling client requests, routing them to the appropriate services, and ensuring security, validation, and logging. In this system, the gateway receives incoming HTTP requests, processes them, and forwards them to the custom server built using FastAPI.

## Key API Usages

### 1. Receiving a Request from the Client
The API Gateway exposes an endpoint that allows clients to send data to the server.

#### Example: Handling a POST Request from Client
```python
from fastapi import FastAPI, Request
import requests

app = FastAPI()

@app.post("/process")
async def process_request(request: Request):
    data = await request.json()
    return {"message": "Request received", "data": data}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/process" \
     -H "Content-Type: application/json" \
     -d '{"data": "sample input"}'
```

**Example Response:**
```json
{
    "message": "Request received",
    "data": "sample input"
}
```

### 2. Forwarding Requests to the Customized Server
The API Gateway forwards incoming requests to the custom server by making an HTTP request to the backend FastAPI service.

#### Example: Forwarding Requests
```python
FORWARD_URL = "http://localhost:9000/analyze"

@app.post("/forward")
async def forward_request(request: Request):
    data = await request.json()
    response = requests.post(FORWARD_URL, json=data)
    return response.json()
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/forward" \
     -H "Content-Type: application/json" \
     -d '{"text": "Analyze this data"}'
```

**Example Response from Backend Server:**
```json
{
    "result": "Analysis complete",
    "status": "success"
}
```

## Conclusion
The API Gateway ensures seamless communication between clients and backend services by managing request routing, security, and logging. It serves as a scalable solution for handling and directing requests efficiently within the system.

