"""
Database Package Initialization.
Factory function get_repository() manages active repository instance.
"""

from database.postgres_repository import PostgresRepository
from database.sqlite_repository import SqliteRepository

_SQLITE_REPO = None

def get_repository(db_credentials=None):
    """
    Returns PostgresRepository if primary database is reachable,
    otherwise safely falls back to SqliteRepository.
    """
    global _SQLITE_REPO
    if db_credentials:
        pg_repo = PostgresRepository(
            host=db_credentials.get("host", "localhost"),
            port=int(db_credentials.get("port", 5432)),
            dbname=db_credentials.get("dbname", "postgres"),
            user=db_credentials.get("user", "postgres"),
            password=db_credentials.get("password", "")
        )
        if pg_repo.is_live():
            return pg_repo

    default_pg = PostgresRepository()
    if default_pg.is_live():
        return default_pg

    if _SQLITE_REPO is None:
        _SQLITE_REPO = SqliteRepository()
    return _SQLITE_REPO
