import os

MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_DB = os.environ.get("MYSQL_DB", "student_score_predictor")

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "student_score_secret_key_2026"
)