from mongoengine import connect
from config.settings import get_settings
from pymongo.errors import PyMongoError


def connect_db():
    settings = get_settings()

    db_name = (
        settings.db_name if settings.env == "prod" else f"{settings.db_name}Testing"
    )
    db_host = f"{settings.db_url}/{db_name}?retryWrites=true&w=majority"

    try:
        connect(db=db_name, host=settings.db_url, alias="default")

        print(
            f"Connected to {'production' if settings.env == 'prod' else 'testing'} database at: {db_host}..."
        )
    except PyMongoError as e:
        print(f"Failed to connect to MongoDB: {e}")
