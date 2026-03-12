from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Custom Logging Middleware
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Log before request processing
        print(f"Before processing: Method={request.method}, Path={request.url.path}")
        
        # Process the request
        response = await call_next(request)
        
        # Log after response
        print(f"After response: Method={request.method}, Path={request.url.path}")
        
        return response

# Create FastAPI app
app = FastAPI()

# Add middleware
app.add_middleware(LoggingMiddleware)

# Hello endpoint
@app.get("/hello")
async def hello():
    return {
        "message": "Hello, Welcome to FastAPI!"
    }

# 404 Exception Handler
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={
            "message": "The requested resource was not found"
        }
    )