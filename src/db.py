from dotenv import load_dotenv
_ = load_dotenv(override=True)

import os
from pymongo import MongoClient
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# PostgreSQL Configuration
EntityBase = declarative_base()

postgres_username = os.getenv("POSTGRES_USERNAME")
postgres_password = os.getenv("POSTGRES_PASSWORD")
postgres_host = os.getenv("POSTGRES_HOST")
postgres_port = os.getenv("POSTGRES_PORT")
postgres_db = os.getenv("POSTGRES_DB")

POSTGRES_URL = f"postgresql://{postgres_username}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"

PostgresSession = sessionmaker(autocommit=False, autoflush=False, bind=create_engine(POSTGRES_URL))()

# MongoDB Configuration
mongodb_username = os.getenv("MONGO_USERNAME")
mongodb_password = os.getenv("MONGO_PASSWORD")
mongodb_host = os.getenv("MONGO_HOST")
mongodb_port = os.getenv("MONGO_PORT")
mongodb_db = os.getenv("MONGO_DB")

if mongodb_username and mongodb_password:
    mongodb_username = quote_plus(mongodb_username)
    mongodb_password = quote_plus(mongodb_password)
    MONGO_URL = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_host}:{mongodb_port}/{mongodb_db}"
else:
    MONGO_URL = f"mongodb://{mongodb_host}:{mongodb_port}"

MongoSession = MongoClient(MONGO_URL)[mongodb_db]
