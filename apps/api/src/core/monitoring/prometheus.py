import time
from fastapi import Request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Define metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests processed",
    ["method", "endpoint", "status"]
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, 30.0)
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Exclude metrics and health endpoints from measurements
        path = request.url.path
        if path in ("/metrics", "/health", "/favicon.ico"):
            return await call_next(request)

        method = request.method
        
        # Clean path mapping for low cardinality labels
        endpoint = path
        if path.startswith("/graphql"):
            endpoint = "/graphql"
        elif path.startswith("/shopify"):
            endpoint = "/shopify/*"
        elif path.startswith("/billing"):
            endpoint = "/billing/*"

        start_time = time.time()
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status=response.status_code).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=endpoint).observe(duration)
            return response
        except Exception as e:
            duration = time.time() - start_time
            HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status=500).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=endpoint).observe(duration)
            raise e


def prometheus_metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
