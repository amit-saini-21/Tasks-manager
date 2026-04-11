import os

from dotenv import load_dotenv


load_dotenv()


class Config:
	SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
	DATABASE_URI = os.getenv("DATABASE_URI", "memory://local")
	DB_POOL_MIN = int(os.getenv("DB_POOL_MIN", "1"))
	DB_POOL_MAX = int(os.getenv("DB_POOL_MAX", "10"))
