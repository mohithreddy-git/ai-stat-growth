from pathlib import Path
import sys

# Allow `python scripts/seed.py` from the backend directory without requiring PYTHONPATH.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.base import Base
from app.db.migrations import run_schema_upgrades
from app.db.session import SessionLocal, engine
from app.services.seed import seed_database


if __name__ == "__main__":
    run_schema_upgrades(engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        print(seed_database(db))
