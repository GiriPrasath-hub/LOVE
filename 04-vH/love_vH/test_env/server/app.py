from openenv.core.env_server.http_server import create_app
from fastapi.middleware.cors import CORSMiddleware

try:
    from ..models import TestAction, TestObservation
    from .test_env_environment import TestEnvironment
except ImportError:
    from models import TestAction, TestObservation
    from test_env_environment import TestEnvironment


app = create_app(
    TestEnvironment,
    TestAction,
    TestObservation,
    env_name="test_env",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()