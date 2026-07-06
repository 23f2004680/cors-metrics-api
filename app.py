import time
import uuid
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()

# ------------------------------------
# Allowed Origin
# ------------------------------------

ALLOWED_ORIGIN = "https://dash-6ikh0r.example.com"

# ------------------------------------
# CORS
# ------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------
# Middleware
# ------------------------------------


class MetricsMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):

        start = time.perf_counter()

        response = await call_next(request)

        duration = time.perf_counter() - start

        response.headers["X-Request-ID"] = str(uuid.uuid4())
        response.headers["X-Process-Time"] = f"{duration:.6f}"

        return response


app.add_middleware(MetricsMiddleware)

# ------------------------------------
# Endpoint
# ------------------------------------


@app.get("/stats")
async def stats(values: str = Query(...)):

    nums = [int(x.strip()) for x in values.split(",") if x.strip()]

    count = len(nums)

    total = sum(nums)

    minimum = min(nums)

    maximum = max(nums)

    mean = total / count

    return {
        "email": "23f2004680@ds.study.iitm.ac.in",
        "count": count,
        "sum": total,
        "min": minimum,
        "max": maximum,
        "mean": mean
    }