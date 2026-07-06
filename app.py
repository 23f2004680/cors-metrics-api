import os
import yaml

from dotenv import load_dotenv
import time
import uuid
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
from fastapi.responses import JSONResponse

from pydantic import BaseModel
app = FastAPI()

load_dotenv()

PUBLIC_KEY = """
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4F1RncsS4LlgniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB
-----END PUBLIC KEY-----
"""
# ------------------------------------
# Allowed Origin
# ------------------------------------

ALLOWED_ORIGIN = "https://dash-6ikh0r.example.com"

class TokenRequest(BaseModel):
    token: str
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

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


def to_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).lower() in ("true", "1", "yes", "on")


def convert(key, value):
    if key in ("port", "workers"):
        return int(value)

    if key == "debug":
        return to_bool(value)

    return str(value)
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

@app.post("/verify")
async def verify(request: TokenRequest):

    try:

        payload = jwt.decode(
            request.token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            audience="tds-wqrasmzc.apps.exam.local",
            issuer="https://idp.exam.local"
        )

        return {
            "valid": True,
            "email": payload.get("email"),
            "sub": payload.get("sub"),
            "aud": payload.get("aud")
        }

    except jwt.InvalidTokenError:
        return JSONResponse(
        status_code=401,
        content={"valid": False}
    )

    from fastapi import Request

@app.get("/effective-config")
async def effective_config(request: Request):

    config = DEFAULTS.copy()

    # -----------------------
    # YAML
    # -----------------------

    if os.path.exists("config.development.yaml"):
        with open("config.development.yaml") as f:
            yaml_config = yaml.safe_load(f) or {}

        for k, v in yaml_config.items():
            config[k] = convert(k, v)

    # -----------------------
    # .env
    # -----------------------

    env_mapping = {
        "APP_PORT": "port",
        "APP_WORKERS": "workers",
        "NUM_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }

    for env_key, cfg_key in env_mapping.items():

        value = os.getenv(env_key)

        if value is not None:
            config[cfg_key] = convert(cfg_key, value)

    # -----------------------
    # CLI Overrides
    # -----------------------

    overrides = request.query_params.getlist("set")

    for item in overrides:

        if "=" not in item:
            continue

        key, value = item.split("=", 1)

        config[key] = convert(key, value)

    # Mask secret
    config["api_key"] = "****"

    return config