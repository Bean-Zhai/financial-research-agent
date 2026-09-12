import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_DIRECTORY = PROJECT_ROOT / "database"
DATABASE_PATH = DATABASE_DIRECTORY / "financial_data.db"
SCHEMA_PATH = DATABASE_DIRECTORY / "schema.sql"


def create_database():
    DATABASE_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True
    )

    schema = SCHEMA_PATH.read_text(
        encoding="utf-8"
    )

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            "PRAGMA foreign_keys = ON;"
        )

        connection.executescript(schema)

        table_rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name;
            """
        ).fetchall()

    table_names = [
        row[0]
        for row in table_rows
    ]

    print("Database created successfully.")
    print(f"Database path: {DATABASE_PATH}")
    print(f"Tables: {table_names}")


if __name__ == "__main__":
    create_database()