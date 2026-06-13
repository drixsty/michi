import argparse
import uvicorn
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from core.server import mcp
from core.context import jwt_token_var, org_id_var

# Import tools and resources to register them
import tools.tools
import resources.resources

class AuthContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract JWT and Organization ID from incoming requests
    and populate request-local contextvars.
    """
    async def dispatch(self, request: Request, call_next):
        # Extract from headers
        auth_header = request.headers.get("Authorization")
        org_id_header = request.headers.get("michi-org-id")
        
        jwt_token = None
        if auth_header and auth_header.lower().startswith("bearer "):
            jwt_token = auth_header.split(" ")[1]
            
        # Support query parameters (handy for SSE handshakes)
        if not jwt_token:
            jwt_token = request.query_params.get("token")
        if not org_id_header:
            org_id_header = request.query_params.get("org_id")
            
        # Set task-local variables
        token_token = jwt_token_var.set(jwt_token)
        org_token = org_id_var.set(org_id_header)
        
        try:
            response = await call_next(request)
            return response
        finally:
            # Clean up context to avoid leaks
            jwt_token_var.reset(token_token)
            org_id_var.reset(org_token)

def main():
    parser = argparse.ArgumentParser(description="Michi MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="sse",
        help="Transport mechanism (default: sse)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8002,
        help="Port to run SSE FastAPI on (default: 8002)"
    )
    args = parser.parse_args()
    
    if args.transport == "stdio":
        print("Starting Michi MCP Server in Stdio transport mode...", flush=True)
        mcp.run(transport="stdio")
    else:
        print(f"Starting Michi MCP Server in SSE transport mode on port {args.port}...", flush=True)
        app = FastAPI(
            title="Michi MCP Server",
            description="Model Context Protocol server for the Michi Platform",
            version="1.0.0"
        )
        app.add_middleware(AuthContextMiddleware)
        
        # Mount the FastMCP SSE application
        app.mount("/mcp", mcp.sse_app())
        
        @app.get("/health")
        async def health():
            return {"status": "ok", "service": "mcp-server"}
            
        uvicorn.run(app, host="0.0.0.0", port=args.port)

if __name__ == "__main__":
    main()
