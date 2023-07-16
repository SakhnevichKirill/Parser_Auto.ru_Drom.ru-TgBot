import os
from flask import Flask

database_name = "autoparser"
ip_address = "172.18.0.3"

app = Flask(__name__)
SQLALCHEMY_DATABASE_URI = os.getenv(
    "DATABASE_URL", f"postgresql://root:root@{ip_address}:5432/{database_name}"
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

if __name__ == "__main__":
    print("DATABASE_URL: ", SQLALCHEMY_DATABASE_URI)