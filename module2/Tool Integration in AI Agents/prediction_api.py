from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import torch
import torch.nn as nn
import time
import logging
from datetime import datetime


# Initialize FastAPI app
app = FastAPI(
    title="TripZen Fault Prediction API",
    version="1.2",
    description="REST API for predicting machine failures using a PyTorch model"
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


MODEL_VERSION = "1.2"
MODEL_PATH = "fault_model_v1.2.pth"


class FaultClassifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(3, 8),
            nn.ReLU(),
            nn.Linear(8, 2),
        )

    def forward(self, x):
        return self.network(x)


# Load PyTorch model weights
model = FaultClassifier()
model_loaded = False

try:
    state_dict = torch.load(MODEL_PATH, map_location="cpu")
    model.load_state_dict(state_dict)
    model.eval()
    model_loaded = True
    logger.info(f"Model loaded successfully | version={MODEL_VERSION}")

except Exception as e:
    logger.error(f"Failed to load model: {e}")
    model_loaded = False


class PredictRequest(BaseModel):
    temperature: float
    vibration: float
    pressure: float


class PredictResponse(BaseModel):
    prediction: int
    confidence: float
    model_version: str
    latency_microseconds: float
    status: int


class ErrorResponse(BaseModel):
    error: str
    status: int


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "error": "Validation failed: request body must contain numeric temperature, vibration, and pressure",
            "status": 400
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status": exc.status_code
        }
    )


@app.get("/health")
async def health():
    if not model_loaded:
        return JSONResponse(
            status_code=503,
            content={
                "service": "TripZen Fault Prediction API",
                "model_version": MODEL_VERSION,
                "model_loaded": False,
                "status": 503,
                "message": "Model is unavailable"
            }
        )

    return {
        "service": "TripZen Fault Prediction API",
        "model_version": MODEL_VERSION,
        "model_loaded": True,
        "status": 200,
        "message": "Service is healthy"
    }


def validate_sensor_inputs(request: PredictRequest):
    if not -50 <= request.temperature <= 50:
        raise HTTPException(
            status_code=400,
            detail="Validation failed: temperature must be between -50 and 50"
        )

    if not 0 <= request.vibration <= 100:
        raise HTTPException(
            status_code=400,
            detail="Validation failed: vibration must be between 0 and 100"
        )

    if not 0 <= request.pressure <= 200:
        raise HTTPException(
            status_code=400,
            detail="Validation failed: pressure must be between 0 and 200"
        )


@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    if not model_loaded:
        raise HTTPException(
            status_code=503,
            detail="Model is unavailable. Please try again later."
        )

    validate_sensor_inputs(request)

    start_time = time.perf_counter()

    input_tensor = torch.tensor(
        [[request.temperature, request.vibration, request.pressure]],
        dtype=torch.float32
    )

    with torch.no_grad():
        logits = model(input_tensor)
        probabilities = torch.softmax(logits, dim=1)

        confidence_tensor, prediction_tensor = torch.max(probabilities, dim=1)

        prediction = int(prediction_tensor.item())
        confidence = float(confidence_tensor.item())

    latency_microseconds = (time.perf_counter() - start_time) * 1_000_000

    logger.info(
        "Prediction request processed | "
        f"timestamp={datetime.utcnow().isoformat()} | "
        f"model_version={MODEL_VERSION} | "
        f"temperature={request.temperature} | "
        f"vibration={request.vibration} | "
        f"pressure={request.pressure} | "
        f"prediction={prediction} | "
        f"confidence={confidence:.4f} | "
        f"latency_microseconds={latency_microseconds:.2f}"
    )

    return {
        "prediction": prediction,
        "confidence": round(confidence, 4),
        "model_version": MODEL_VERSION,
        "latency_microseconds": round(latency_microseconds, 2),
        "status": 200
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )