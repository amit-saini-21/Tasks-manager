import os

from dotenv import load_dotenv


load_dotenv()


class Config:
	SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
	DATABASE_URI = os.getenv("DATABASE_URI", "memory://local")
