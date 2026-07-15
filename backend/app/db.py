from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./ticket_routing.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def sync_schema():
    """
    Add any model columns missing from the existing SQLite file.

    Base.metadata.create_all only creates tables that don't exist yet - it
    never alters an existing table. There's no Alembic in this project, so
    newly added nullable columns (e.g. the Jira sync fields) need this
    lightweight ALTER TABLE step or the app breaks against a pre-existing
    ticket_routing.db.
    """
    inspector = inspect(engine)
    for table in Base.metadata.tables.values():
        if table.name not in inspector.get_table_names():
            continue
        existing_columns = {col["name"] for col in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in existing_columns:
                continue
            column_type = column.type.compile(engine.dialect)
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE {table.name} ADD COLUMN {column.name} {column_type}"))
