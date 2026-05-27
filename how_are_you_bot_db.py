import os

from sqlalchemy import create_engine

db = create_engine(os.getenv('PG_DSN'))


def migrate_database():
    from yoyo import read_migrations
    from yoyo import get_backend

    backend = get_backend(os.getenv('PG_DSN'))
    migrations = read_migrations('./migrations')

    with backend.lock():
        # Apply any outstanding migrations
        backend.apply_migrations(backend.to_apply(migrations))




