from fastapi import FastAPI
import uvicorn
from routes import setup_routes
from utils import setup_middleware


def create_app() -> FastAPI:
    app = FastAPI()
    setup_middleware(app)
    setup_routes(app)
    return app


if __name__ == "__main__":
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=3000)
