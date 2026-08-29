import asyncio

import pytest
from sqlalchemy import select

from app.ai.providers import ProviderError, _validated_structured
from app.ai.quality import GeneratedMCQ, QuestionQualityValidator
from app.db.session import SessionLocal
from app.models import AssessmentItemReview, CompetencyEvidence, CompetencyScoreHistory, RecommendationSnapshot


def login(client, email):
    response = client.post("/api/auth/login", json={"email": email, "password": "Demo@123"})
    assert response.status_code == 200
    body = response.json()
    return body["user"], {"Authorization": f"Bearer {body['access_token']}"}


def test_frac_profile_and_vector_alignment(client):
    user, headers = login(client, "employee.demo@aistatgrowth.gov.in")
    frac = client.get(f"/api/users/{user['id']}/frac-profile", headers=headers)
    assert frac.status_code == 200
    body = frac.json()
    assert body["role"] == "Assistant Director — Statistical Analysis"
    assert {item["activity"] for item in body["activities"]} >= {"Survey Data Analysis", "Statistical Validation", "Data Visualization", "Analytical Reporting"}
    assert all(item["required_level"] in range(1, 6) for item in body["activities"])

    vector = client.get(f"/api/users/{user['id']}/competency-vector", headers=headers)
    assert vector.status_code == 200
    payload = vector.json()
    assert len(payload["current_vector"]) == 35
    assert len(payload["target_vector"]) == 35
    assert 0 <= payload["cosine_similarity"] <= 1
    assert 0 <= payload["overall_alignment_score"] <= 100
    assert any(item["competency"] == "GIS" and item["gap"] >= 0 for item in payload["competency_specific_gaps"])


def test_evidence_and_telemetry_deduplicate(client):
    user, headers = login(client, "employee.demo@aistatgrowth.gov.in")
    evidence = client.get(f"/api/users/{user['id']}/evidence", headers=headers)
    assert evidence.status_code == 200
    assert evidence.json() and any(row["source_type"] == "SELF_DECLARATION" for row in evidence.json())
    event = {"eid": "CONTENT_VIEW", "ver": "3.0", "mid": "test-telemetry-mid-001", "actor": {"id": "ignored"}, "context": {}, "object": {"id": "course:1"}, "edata": {"duration": 1}, "tags": []}
    first = client.post("/api/telemetry/events", headers=headers, json=event)
    second = client.post("/api/telemetry/events", headers=headers, json=event)
    assert first.status_code == second.status_code == 200
    assert first.json()["duplicate"] is False and second.json()["duplicate"] is True
    velocity = client.get(f"/api/telemetry/learner/{user['id']}/velocity", headers=headers)
    assert velocity.status_code == 200
    assert velocity.json()["learning_velocity"] >= 0


def test_quality_validator_rejects_invalid_items():
    item = GeneratedMCQ.model_construct(question="Which source claim is supported?", options=["A", "A", "B", "C"], correct_index=0, explanation="Source explanation", competency_id=1, topic="topic", difficulty="medium", source={"document_id": 1, "chunk_id": "1:1"})
    assert not QuestionQualityValidator.validate(item, "A source statement about statistics.").valid
    valid = GeneratedMCQ(question="Which source claim is supported?", options=["A source statement about statistics.", "Not present", "Unspecified", "Different"], correct_index=0, explanation="The source contains this statement.", competency_id=1, topic="topic", difficulty="medium", source={"document_id": 1, "chunk_id": "1:1"})
    assert QuestionQualityValidator.validate(valid, "A source statement about statistics.", known_competency_ids={1}).valid


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"options": ["A", "B", "C"]}, "exactly four options"),
        ({"options": ["A", "B", "C", "D", "E"]}, "exactly four options"),
        ({"correct_index": 4}, "correct_index"),
        ({"options": ["A", "A", "C", "D"]}, "unique"),
        ({"explanation": ""}, "explanation is empty"),
        ({"competency_id": 999}, "competency does not exist"),
        ({"source": {}}, "source provenance is incomplete"),
        ({"question": "What is quantum chromodynamics?", "options": ["Quantum", "A", "B", "C"]}, "not supported"),
    ],
)
def test_quality_validator_rejects_each_invalid_condition(overrides, reason):
    values = {
        "question": "Which source claim is supported?",
        "options": ["A source statement about statistics.", "Not present", "Unspecified", "Different"],
        "correct_index": 0,
        "explanation": "The source contains this statement.",
        "competency_id": 1,
        "topic": "topic",
        "difficulty": "medium",
        "source": {"document_id": 1, "chunk_id": "1:1"},
    }
    values.update(overrides)
    item = GeneratedMCQ.model_construct(**values)
    result = QuestionQualityValidator.validate(item, "A source statement about statistics.", known_competency_ids={1})
    assert not result.valid
    assert any(reason in detail for detail in result.reasons)


class _FlakyProvider:
    name = "test-provider"

    def __init__(self):
        self.calls = 0

    async def generate_text(self, prompt, *, system=""):
        self.calls += 1
        if self.calls == 1:
            return "not json"
        return '{"question":"Which source claim is supported?","options":["A source statement about statistics.","Not present","Unspecified","Different"],"correct_index":0,"explanation":"The source contains this statement.","competency_id":1,"topic":"topic","difficulty":"medium","source":{"document_id":1,"chunk_id":"1:1"}}'


class _AlwaysInvalidProvider:
    name = "test-provider"

    async def generate_text(self, prompt, *, system=""):
        return "{not valid json"


def test_structured_provider_retries_once_then_returns_typed_model():
    provider = _FlakyProvider()
    result = asyncio.run(_validated_structured(provider, "prompt", GeneratedMCQ, "system"))
    assert isinstance(result, GeneratedMCQ)
    assert provider.calls == 2


def test_structured_provider_fails_safely_after_invalid_retry():
    with pytest.raises(ProviderError):
        asyncio.run(_validated_structured(_AlwaysInvalidProvider(), "prompt", GeneratedMCQ, "system"))


def test_upload_validation_and_studio_rbac(client):
    trainer, trainer_headers = login(client, "trainer.demo@aistatgrowth.gov.in")
    employee, employee_headers = login(client, "employee.demo@aistatgrowth.gov.in")
    unsupported_extension = client.post("/api/documents/upload", headers=trainer_headers, files={"upload": ("payload.exe", b"not executable", "application/octet-stream")})
    assert unsupported_extension.status_code == 415
    mismatched_mime = client.post("/api/documents/upload", headers=trainer_headers, files={"upload": ("payload.pdf", b"not a pdf", "text/html")})
    assert mismatched_mime.status_code == 415
    for path, method, payload in [
        ("/api/assessment-items/review-queue", "get", None),
        ("/api/quizzes/publish", "post", {"title": "Blocked", "item_ids": [1]}),
    ]:
        response = getattr(client, method)(path, headers=employee_headers, json=payload) if payload else getattr(client, method)(path, headers=employee_headers)
        assert response.status_code == 403
    assert employee["role"] == "EMPLOYEE" and trainer["role"] == "TRAINER"


def test_trainer_document_review_publish_quiz_and_admin_aggregates(client):
    trainer, trainer_headers = login(client, "trainer.demo@aistatgrowth.gov.in")
    pdf = b"%PDF-1.4\\n1 0 obj\\n<< /Length 120 >>\\nstream\\n(Official statistics use evidence-based sampling and validation.) Tj\\nendstream\\nendobj\\n%%EOF"
    upload = client.post("/api/documents/upload", headers=trainer_headers, files={"upload": ("sampling-guide.pdf", pdf, "application/pdf")})
    assert upload.status_code == 200, upload.text
    document = upload.json()
    upload_events = client.get(f"/api/telemetry/events/{trainer['id']}", headers=trainer_headers)
    assert upload_events.status_code == 200 and any(event["eid"] == "DOCUMENT_UPLOAD" for event in upload_events.json())
    processed = client.post(f"/api/documents/{document['id']}/process", headers=trainer_headers)
    assert processed.status_code == 200, processed.text
    assert processed.json()["status"] == "processed" and processed.json()["chunk_count"] >= 1
    generated = client.post("/api/assessment-items/generate", headers=trainer_headers, json={"document_id": document["id"], "competency_id": 11, "count": 11, "topic": "sampling and validation"})
    assert generated.status_code == 200, generated.text
    items = generated.json()
    assert len(items) == 11
    assert all(item["status"] == "PENDING_REVIEW" and item["source"]["document_id"] == document["id"] and item["source"]["chunk_id"] for item in items)
    assert all(item["source"]["page_number"] == 1 for item in items)
    with SessionLocal() as db:
        review_actions = db.scalars(select(AssessmentItemReview.action).where(AssessmentItemReview.assessment_item_id.in_([item["id"] for item in items]))).all()
        assert {action for action in review_actions} >= {"GENERATED", "VALIDATED", "PENDING_REVIEW"}
    queue = client.get("/api/assessment-items/review-queue", headers=trainer_headers)
    assert queue.status_code == 200 and len(queue.json()) >= 11
    rejected = client.post(f"/api/assessment-items/{items[0]['id']}/reject", headers=trainer_headers, json={"note": "Rejected for review test"})
    assert rejected.status_code == 200 and rejected.json()["status"] == "REJECTED"
    rejected_publish = client.post("/api/quizzes/publish", headers=trainer_headers, json={"title": "Rejected quiz", "item_ids": [items[0]["id"]]})
    assert rejected_publish.status_code == 409
    unreviewed_publish = client.post("/api/quizzes/publish", headers=trainer_headers, json={"title": "Unreviewed quiz", "item_ids": [items[1]["id"]]})
    assert unreviewed_publish.status_code == 409
    for item in items[1:]:
        approved = client.post(f"/api/assessment-items/{item['id']}/approve", headers=trainer_headers, json={"note": "Reviewed for source support"})
        assert approved.status_code == 200 and approved.json()["status"] == "APPROVED"
    quiz = client.post("/api/quizzes/publish", headers=trainer_headers, json={"title": "Source-grounded practice", "item_ids": [item["id"] for item in items[1:]]})
    assert quiz.status_code == 200, quiz.text
    employee, employee_headers = login(client, "official03.demo@aistatgrowth.gov.in")
    before_recommendations = client.get(f"/api/users/{employee['id']}/recommendations", headers=employee_headers).json()
    before_gaps = client.get(f"/api/users/{employee['id']}/skill-gaps", headers=employee_headers).json()
    before_by_code = {gap["code"]: gap for gap in before_gaps}
    with SessionLocal() as db:
        before_snapshot_count = len(db.scalars(select(RecommendationSnapshot).where(RecommendationSnapshot.employee_id == employee["id"])).all())
    quiz_body = client.get(f"/api/quizzes/{quiz.json()['id']}", headers=employee_headers)
    assert quiz_body.status_code == 200 and len(quiz_body.json()["items"]) == 10
    employee_events = client.get(f"/api/telemetry/events/{employee['id']}", headers=employee_headers)
    assert employee_events.status_code == 200 and any(event["eid"] == "CONTENT_VIEW" for event in employee_events.json())
    result = client.post(f"/api/quizzes/{quiz.json()['id']}/submit", headers=employee_headers, json={"answers": {str(item["id"]): 0 for item in quiz_body.json()["items"]}})
    assert result.status_code == 200 and result.json()["correct_answers"] == 10
    after_profile = client.get(f"/api/users/{employee['id']}/competencies", headers=employee_headers).json()
    after_python = next(item for item in after_profile["competencies"] if item["code"] == "PYTHON")
    assert after_python["current_score"] > 45.0 and after_python["evidence_count"] >= 2
    after_gaps = client.get(f"/api/users/{employee['id']}/skill-gaps", headers=employee_headers).json()
    after_by_code = {gap["code"]: gap for gap in after_gaps}
    assert after_by_code["PYTHON"]["gap"] < before_by_code["PYTHON"]["gap"]
    after_recommendations = client.get(f"/api/users/{employee['id']}/recommendations", headers=employee_headers).json()
    before_python_recommendations = [item for item in before_recommendations if item["competency"] == "Python"]
    if before_python_recommendations:
        assert all(item["competency"] != "Python" for item in after_recommendations)
    with SessionLocal() as db:
        after_snapshot_count = len(db.scalars(select(RecommendationSnapshot).where(RecommendationSnapshot.employee_id == employee["id"])).all())
        assert after_snapshot_count > before_snapshot_count
        quiz_evidence = db.scalars(select(CompetencyEvidence).where(CompetencyEvidence.employee_id == employee["id"], CompetencyEvidence.competency_id == 11, CompetencyEvidence.source_type == "QUIZ")).all()
        quiz_history = db.scalars(select(CompetencyScoreHistory).where(CompetencyScoreHistory.user_id == employee["id"], CompetencyScoreHistory.competency_id == 11, CompetencyScoreHistory.source == "quiz")).all()
        assert quiz_evidence and quiz_history and quiz_history[-1].evidence_id == quiz_evidence[-1].id
    grounded = client.post("/api/ai/chat", headers=employee_headers, json={"message": "What does sampling support?", "mode": "document", "document_id": document["id"]})
    assert grounded.status_code == 200 and grounded.json()["sources"] and grounded.json()["sources"][0]["page_number"] == 1
    unsupported = client.post("/api/ai/chat", headers=employee_headers, json={"message": "Explain quantum chromodynamics", "mode": "document", "document_id": document["id"]})
    assert unsupported.status_code == 404
    admin, admin_headers = login(client, "admin.demo@aistatgrowth.gov.in")
    for path in ["/api/admin/overview", "/api/admin/departments", "/api/admin/skill-gaps", "/api/admin/training-effectiveness", "/api/admin/forecast", "/api/telemetry/organization/summary", "/api/telemetry/organization/recent"]:
        response = client.get(path, headers=admin_headers)
        assert response.status_code == 200, (path, response.text)


def test_demo_reset_is_admin_only_and_restores_clean_baseline(client):
    employee, employee_headers = login(client, "employee.demo@aistatgrowth.gov.in")
    forbidden = client.post("/api/demo/reset", headers=employee_headers)
    assert forbidden.status_code == 403
    _, admin_headers = login(client, "admin.demo@aistatgrowth.gov.in")
    reset = client.post("/api/demo/reset", headers=admin_headers)
    assert reset.status_code == 200, reset.text
    body = reset.json()
    assert body["status"] == "reset"
    assert body["runtime_counts"]["learning_progress"] == 0
    assert body["runtime_counts"]["assessment_attempts"] == 0
    assert body["runtime_counts"]["uploaded_documents"] == 0
    assert body["runtime_counts"]["telemetry_events"] == 0
    progress = client.get(f"/api/users/{employee['id']}/learning-progress", headers=employee_headers)
    events = client.get(f"/api/telemetry/events/{employee['id']}", headers=employee_headers)
    profile = client.get(f"/api/users/{employee['id']}/competencies", headers=employee_headers)
    assert progress.status_code == events.status_code == profile.status_code == 200
    assert progress.json() == [] and events.json() == []
    by_code = {item["code"]: item for item in profile.json()["competencies"]}
    assert by_code["GIS"]["current_score"] == 31.0 and by_code["PYTHON"]["current_score"] == 45.0
