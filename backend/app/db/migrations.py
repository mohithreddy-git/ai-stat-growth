from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


# This project intentionally avoids a heavyweight migration dependency during the
# zero-cost prototype. The helper is additive and safe to run at every startup.
_ADDITIVE_COLUMNS = {
    "competencies": {
        "competency_type": "VARCHAR(32) NOT NULL DEFAULT 'Functional'",
        "domain_id": "INTEGER",
        "required_level_id": "INTEGER",
    },
    "employee_competencies": {
        "confidence": "FLOAT NOT NULL DEFAULT 0.5",
        "evidence_count": "INTEGER NOT NULL DEFAULT 0",
    },
    "competency_score_history": {
        "evidence_id": "INTEGER",
        "calculation": "TEXT NOT NULL DEFAULT ''",
    },
    "document_chunks": {
        "embedding_json": "JSON",
    },
    "recommendations": {
        "factors": "JSON NOT NULL DEFAULT '{}'",
        "activities": "JSON NOT NULL DEFAULT '[]'",
        "generated_at": "DATETIME",
    },
    "quiz_attempts": {
        "published_quiz_id": "INTEGER",
        "language": "VARCHAR(8) NOT NULL DEFAULT 'en'",
    },
    "assessment_questions": {
        "localizations": "JSON NOT NULL DEFAULT '{}'",
    },
    "assessment_attempts": {
        "language": "VARCHAR(8) NOT NULL DEFAULT 'en'",
    },
    "courses": {
        "localizations": "JSON NOT NULL DEFAULT '{}'",
    },
    "training_programmes": {
        "localizations": "JSON NOT NULL DEFAULT '{}'",
    },
    "assessment_items": {
        "localizations": "JSON NOT NULL DEFAULT '{}'",
    },
    "skill_forecasts": {
        "period": "VARCHAR(32) NOT NULL DEFAULT '2026-2030'",
        "source": "VARCHAR(120) NOT NULL DEFAULT 'prototype_seed'",
        "confidence": "FLOAT NOT NULL DEFAULT 0.5",
    },
}


def run_schema_upgrades(engine: Engine) -> None:
    inspector = inspect(engine)
    with engine.begin() as connection:
        for table_name, columns in _ADDITIVE_COLUMNS.items():
            if not inspector.has_table(table_name):
                continue
            existing = {column["name"] for column in inspect(connection).get_columns(table_name)}
            for column_name, definition in columns.items():
                if column_name not in existing:
                    connection.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {definition}'))
