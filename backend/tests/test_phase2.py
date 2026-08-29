from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models import Competency
from app.services.skill_gaps import gap_priority, severity_for_gap


def login(client, email="employee.demo@aistatgrowth.gov.in"):
    response = client.post("/api/auth/login", json={"email": email, "password": "Demo@123"})
    assert response.status_code == 200
    body = response.json()
    return body["user"], {"Authorization": f"Bearer {body['access_token']}"}


def test_employee_profile_and_competency_baseline(client):
    user, headers = login(client)
    profile = client.get(f"/api/users/{user['id']}", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["full_name"] == "Dr. Ananya Sharma"
    assert profile.json()["department"] == "National Statistical Office"
    assert profile.json()["years_experience"] == 5.0

    competency = client.get(f"/api/users/{user['id']}/competencies", headers=headers)
    assert competency.status_code == 200
    body = {item["code"]: item for item in competency.json()["competencies"]}
    assert len(body) >= 25
    assert body["PYTHON"]["current_score"] == 45.0
    assert body["GIS"]["current_score"] == 31.0
    assert body["ARTIFICIAL_INTELLIGENCE"]["current_score"] == 38.0
    assert body["DATA_VISUALIZATION"]["current_score"] == 72.0


def test_competency_domain_summary_is_database_driven(client):
    user, headers = login(client)
    response = client.get(f"/api/users/{user['id']}/competency-domain-summary", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    actual = {item["name"]: item for item in payload["domains"]}
    assert {name: item["count"] for name, item in actual.items()} == {
        "Statistical": 10,
        "Technical": 14,
        "Digital Governance": 5,
        "Behavioural & Managerial": 6,
    }
    assert payload["total_competencies"] == 35
    with SessionLocal() as db:
        database_counts = dict(db.execute(select(Competency.category, func.count(Competency.id)).group_by(Competency.category)).all())
        database_total = db.scalar(select(func.count(Competency.id)))
    assert database_counts == {name: item["count"] for name, item in actual.items()}
    assert database_total == payload["total_competencies"]
    assert all(item["average_current_score"] is not None and item["average_target_score"] is not None for item in actual.values())


def test_gap_thresholds_and_priority_are_server_calculated(client):
    user, headers = login(client)
    response = client.get(f"/api/users/{user['id']}/skill-gaps", headers=headers)
    assert response.status_code == 200
    gaps = response.json()
    by_code = {item["code"]: item for item in gaps}
    assert by_code["GIS"]["gap"] == 49.0
    assert by_code["GIS"]["severity"] == "critical"
    assert by_code["PYTHON"]["gap"] == 35.0
    assert by_code["PYTHON"]["severity"] == "critical"
    assert by_code["SQL"]["gap"] == 16.0
    assert by_code["SQL"]["severity"] == "medium"
    assert all(0 <= item["priority_score"] <= 100 for item in gaps)
    assert gaps[0]["priority_score"] >= gaps[-1]["priority_score"]
    assert by_code["GIS"]["role_relevance"] == 95.0
    assert "current score" in by_code["GIS"]["explanation"]


def test_cross_domain_assessment_submission_updates_competencies_and_result(client):
    user, headers = login(client)
    assessments = client.get("/api/assessments", headers=headers)
    assert assessments.status_code == 200
    baseline = assessments.json()[0]
    assert baseline["question_count"] >= 20

    started = client.post("/api/assessments/start", headers=headers, json={"assessment_id": baseline["id"]})
    assert started.status_code == 200
    attempt = started.json()
    questions = attempt["assessment"]["questions"]
    assert len(questions) == baseline["question_count"]
    assert {question["category"] for question in questions} >= {"Statistical", "Technical", "Digital Governance", "Behavioural & Managerial"}

    answers = [{"question_id": question["id"], "answer": question["options"][0]} for question in questions]
    result = client.post(f"/api/assessments/{attempt['attempt_id']}/submit", headers=headers, json={"answers": answers})
    assert result.status_code == 200
    body = result.json()
    assert body["status"] == "completed"
    assert body["percentage"] == 100.0
    assert body["correct_answers"] == body["total_questions"]
    assert body["competency_results"]
    assert all(item["updated_score"] >= item["previous_score"] for item in body["competency_results"])
    assert any(item["delta"] > 0 for item in body["competency_results"])

    result_read = client.get(f"/api/assessments/{attempt['attempt_id']}/result", headers=headers)
    assert result_read.status_code == 200
    assert result_read.json()["attempt_id"] == attempt["attempt_id"]

    competency = client.get(f"/api/users/{user['id']}/competencies", headers=headers).json()
    assert any(item["delta_from_previous"] and item["delta_from_previous"] > 0 for item in competency["competencies"])
    events = client.get(f"/api/telemetry/events/{user['id']}", headers=headers)
    assert events.status_code == 200
    assert {event["eid"] for event in events.json()} >= {"ASSESSMENT_START", "RESPONSE", "ASSESSMENT_END", "SKILL_PROFILE_UPDATE"}


def test_recommendations_include_both_prototype_sources_and_explainability(client):
    user, headers = login(client)
    response = client.get(f"/api/users/{user['id']}/recommendations", headers=headers)
    assert response.status_code == 200
    recommendations = response.json()
    assert recommendations
    assert {item["resource_type"] for item in recommendations} >= {"course", "training_programme"}
    assert all(item["reason"] and item["expected_outcome"] for item in recommendations)
    assert all(0 <= item["relevance_score"] <= 100 for item in recommendations)
    assert all("current_score" in item and "required_score" in item for item in recommendations)
    assert recommendations[0]["relevance_score"] >= recommendations[-1]["relevance_score"]


def test_learning_progress_upsert_is_persisted_and_rbac_blocks_cross_user_access(client):
    user, headers = login(client)
    recommendations = client.get(f"/api/users/{user['id']}/recommendations", headers=headers).json()
    resource = recommendations[0]
    payload = {
        "resource_type": resource["resource_type"],
        "resource_id": resource["id"],
        "status": "in_progress",
        "completion_percent": 25,
        "learning_hours": 1.0,
    }
    saved = client.post(f"/api/users/{user['id']}/learning-progress", headers=headers, json=payload)
    assert saved.status_code == 200
    assert saved.json()["status"] == "in_progress"
    listed = client.get(f"/api/users/{user['id']}/learning-progress", headers=headers)
    assert listed.status_code == 200
    assert any(row["resource_id"] == resource["id"] for row in listed.json())

    other_user_id = client.post("/api/auth/login", json={"email": "official02.demo@aistatgrowth.gov.in", "password": "Demo@123"}).json()["user"]["id"]
    blocked = client.get(f"/api/users/{other_user_id}/skill-gaps", headers=headers)
    assert blocked.status_code == 403


def test_assessment_requires_all_questions_and_invalid_option_is_rejected(client):
    _, headers = login(client)
    assessment = client.get("/api/assessments", headers=headers).json()[0]
    attempt = client.post("/api/assessments/start", headers=headers, json={"assessment_id": assessment["id"]}).json()
    questions = attempt["assessment"]["questions"]
    missing = client.post(f"/api/assessments/{attempt['attempt_id']}/submit", headers=headers, json={"answers": []})
    assert missing.status_code == 422

    invalid = [{"question_id": question["id"], "answer": question["options"][0]} for question in questions]
    invalid[0]["answer"] = "Not an available option"
    rejected = client.post(f"/api/assessments/{attempt['attempt_id']}/submit", headers=headers, json={"answers": invalid})
    assert rejected.status_code == 400


def test_gap_severity_and_priority_boundaries_are_configured():
    assert [severity_for_gap(value) for value in (30, 29.9, 20, 19.9, 10, 9.9)] == ["critical", "high", "high", "medium", "medium", "low"]
    assert gap_priority(100, 100, 100, 100, 100) == 100.0
    assert gap_priority(0, 0, 0, 0, 0) == 0.0
    assert gap_priority(75, 95, 95, 80, 85) == 83.8


def test_dashboard_aggregates_live_profile_gaps_recommendations_and_learning(client):
    user, headers = login(client)
    response = client.get(f"/api/users/{user['id']}/dashboard", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["profile"]["full_name"] == "Dr. Ananya Sharma"
    assert body["competency"]["overall_readiness"] > 0
    assert body["skill_gaps"]
    assert body["recommendations"]
    assert body["learning_progress"]
    assert body["completed_courses"] >= 2
    assert body["learning_hours"] > 0


def test_learning_source_endpoints_return_api_shaped_prototype_records(client):
    _, headers = login(client)
    courses = client.get("/api/courses", headers=headers)
    programmes = client.get("/api/training-programmes", headers=headers)
    competencies = client.get("/api/competencies", headers=headers)
    assert courses.status_code == programmes.status_code == competencies.status_code == 200
    assert len(courses.json()) >= 30
    assert len(programmes.json()) >= 15
    assert len(competencies.json()) >= 35
    assert all(item["is_prototype"] and item["source"].lower().find("prototype") >= 0 for item in courses.json() + programmes.json())
