import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/task_manager")
SECRET_KEY = os.getenv("SECRET_KEY", "63f4945d921d599f27ae4fdf5bada3f1")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7