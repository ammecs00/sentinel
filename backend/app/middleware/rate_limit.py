from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Production-safe rate limiting middleware with Proxy support
    """

    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[datetime]] = {}
        # Trust traffic from Docker internal networks
        self.trusted_proxies = ("172.", "10.", "192.168.", "127.0.0.1")
        
        self.excluded_paths = {
            "/health",
            "/api/v1/auth/me",
            "/docs",
            "/redoc",
            "/openapi.json"
        }

    def _is_internal(self, ip: str) -> bool:
        """Check if IP is from internal network"""
        return ip.startswith(self.trusted_proxies)
    
    def _is_excluded_path(self, path: str) -> bool:
        return path in self.excluded_paths or path.startswith("/static/")

    def _get_client_ip(self, request: Request) -> str:
        """
        Get real client IP, respecting X-Forwarded-For only from trusted proxies.
        """
        client_host = request.client.host
        
        # If request comes from a trusted proxy (Nginx), use X-Forwarded-For
        if self._is_internal(client_host):
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                # Get the first IP in the list (original client)
                return forwarded_for.split(",")[0].strip()
        
        return client_host

    def _get_identity(self, request: Request) -> str:
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"

        return f"ip:{self._get_client_ip(request)}"

    async def dispatch(self, request: Request, call_next):
        # Skip excluded paths
        if self._is_excluded_path(request.url.path):
            return await call_next(request)

        # We do NOT skip internal IPs here anymore, because Nginx is internal.
        # We now identify based on the _real_ IP resolved in _get_identity.
        
        identity = self._get_identity(request)
        now = datetime.utcnow()

        # Remove timestamps older than 1 minute
        bucket = self.requests.get(identity, [])
        bucket = [t for t in bucket if now - t < timedelta(minutes=1)]

        if len(bucket) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for {identity} on path {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": "60"}
            )

        bucket.append(now)
        self.requests[identity] = bucket

        return await call_next(request)