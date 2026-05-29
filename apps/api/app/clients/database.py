from sqlalchemy import text
from sqlalchemy.orm import Session


def ping_database(db: Session) -> bool:
    db.execute(text("SELECT 1"))
    return True

