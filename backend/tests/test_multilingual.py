from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import QuizAttempt


def login(client, email="official02.demo@aistatgrowth.gov.in"):
    response = client.post("/api/auth/login", json={"email": email, "password": "Demo@123"})
    assert response.status_code == 200
    body = response.json()
    return body["user"], {"Authorization": f"Bearer {body['access_token']}"}


def test_default_english_hindi_resource_localization_and_invalid_fallback(client):
    user, headers = login(client)
    english = client.get(f"/api/users/{user['id']}/recommendations", headers=headers)
    hindi = client.get(f"/api/users/{user['id']}/recommendations?language=hi", headers=headers)
    invalid = client.get(f"/api/users/{user['id']}/recommendations?language=bn", headers=headers)
    assert english.status_code == hindi.status_code == invalid.status_code == 200
    assert english.json()[0]["requested_language"] == "en"
    assert hindi.json()[0]["requested_language"] == "hi"
    assert invalid.json()[0]["requested_language"] == "en"

    course_en = client.get("/api/courses?language=en", headers=headers).json()[0]
    course_hi = client.get("/api/courses?language=hi", headers=headers).json()[0]
    course_invalid = client.get("/api/courses?language=ta", headers=headers).json()[0]
    assert course_en["title"] == "Python for Statistical Analysis"
    assert course_hi["title"] == "सांख्यिकीय विश्लेषण के लिए पायथन"
    assert course_hi["description"] == "सांख्यिकीय डेटा विश्लेषण में उपयोग की जाने वाली पायथन तकनीकों को सीखें।"
    assert course_hi["localization_label"] == "Prototype multilingual content"
    assert course_hi["title_en"] == course_en["title"]
    assert course_hi["title_hi"] == course_hi["title"]
    assert course_invalid["requested_language"] == "en" and course_invalid["title"] == course_en["title"]

    # Resources without curated Hindi content safely remain English.
    gis = next(item for item in client.get("/api/courses?language=hi", headers=headers).json() if item["course_id"] != "IGOT-PROT-001")
    assert gis["localized"] is False and gis["title"] == gis["title_en"]


def test_same_recommendation_ranking_is_rendered_in_english_and_hindi(client):
    user, headers = login(client, "employee.demo@aistatgrowth.gov.in")
    english = client.get(f"/api/users/{user['id']}/recommendations?language=en", headers=headers).json()
    hindi = client.get(f"/api/users/{user['id']}/recommendations?language=hi", headers=headers).json()
    ranking_fields = lambda rows: [(row["resource_type"], row["id"], row["competency_id"], row["relevance_score"], row["priority_score"]) for row in rows]
    assert ranking_fields(english) == ranking_fields(hindi)
    python_en = next(row for row in english if row["external_id"] == "IGOT-PROT-001")
    python_hi = next(row for row in hindi if row["external_id"] == "IGOT-PROT-001")
    assert python_en["title"] == "Python for Statistical Analysis"
    assert python_hi["title"] == "सांख्यिकीय विश्लेषण के लिए पायथन"
    assert python_hi["description"] != python_en["description"]
    assert python_hi["reason"] != python_en["reason"]
    assert python_hi["explanation_data"] == python_en["explanation_data"]


def test_bilingual_quiz_uses_same_answer_index_and_score(client):
    user, headers = login(client)
    english = client.get("/api/quizzes/1?language=en", headers=headers)
    hindi = client.get("/api/quizzes/1?language=hi", headers=headers)
    assert english.status_code == hindi.status_code == 200
    english_item = english.json()["items"][0]
    hindi_item = hindi.json()["items"][0]
    assert english.json()["requested_language"] == "en"
    assert hindi.json()["requested_language"] == "hi"
    assert english_item["question"] != hindi_item["question"]
    assert english_item["options"][0] != hindi_item["options"][0]
    assert english_item["id"] == hindi_item["id"]
    assert hindi_item["localized"] is True

    english_result = client.post("/api/quizzes/1/submit", headers=headers, json={"answers": {str(english_item["id"]): 0}, "language": "en"})
    hindi_result = client.post("/api/quizzes/1/submit", headers=headers, json={"answers": {str(hindi_item["id"]): 0}, "language": "hi"})
    assert english_result.status_code == hindi_result.status_code == 200
    assert english_result.json()["score"] == hindi_result.json()["score"] == 100.0
    assert hindi_result.json()["requested_language"] == "hi"
    assert "दस्तावेजित" in hindi_result.json()["explanations"][0]["explanation"]
    assert english_result.json()["explanations"][0]["correct_index"] == hindi_result.json()["explanations"][0]["correct_index"] == 0
    with SessionLocal() as db:
        attempts = db.scalars(select(QuizAttempt).where(QuizAttempt.user_id == user["id"], QuizAttempt.published_quiz_id == 1)).all()
        assert {attempt.language for attempt in attempts} >= {"en", "hi"}


def test_language_switch_does_not_reset_learning_progress_or_rbac(client):
    user, headers = login(client, "employee.demo@aistatgrowth.gov.in")
    saved = client.post(f"/api/users/{user['id']}/learning-progress", headers=headers, json={"resource_type": "course", "resource_id": 3, "status": "in_progress", "completion_percent": 35, "learning_hours": 1.5})
    assert saved.status_code == 200
    english = client.get(f"/api/users/{user['id']}/recommendations?language=en", headers=headers).json()
    hindi = client.get(f"/api/users/{user['id']}/recommendations?language=hi", headers=headers).json()
    english_resource = next(row for row in english if row["external_id"] == "IGOT-PROT-003")
    hindi_resource = next(row for row in hindi if row["external_id"] == "IGOT-PROT-003")
    assert english_resource["progress_status"] == hindi_resource["progress_status"] == "in_progress"
    assert english_resource["completion_percent"] == hindi_resource["completion_percent"] == 35.0
    assert [(row["id"], row["relevance_score"]) for row in english] == [(row["id"], row["relevance_score"]) for row in hindi]
    assert client.get("/api/admin/overview", headers=headers).status_code == 403


def test_statbot_general_language_and_fallback(client):
    _, headers = login(client)
    english = client.post("/api/ai/chat", headers=headers, json={"message": "Explain stratified sampling in simple terms.", "mode": "general", "language": "en"})
    hindi = client.post("/api/ai/chat", headers=headers, json={"message": "स्तरीकृत नमूनाकरण समझाइए।", "mode": "general", "language": "hi"})
    invalid = client.post("/api/ai/chat", headers=headers, json={"message": "Explain stratified sampling in simple terms.", "mode": "general", "language": "bn"})
    assert english.status_code == hindi.status_code == invalid.status_code == 200
    assert english.json()["requested_language"] == "en"
    assert hindi.json()["requested_language"] == "hi"
    assert "स्तरीकृत नमूनाकरण" in hindi.json()["answer"]
    assert invalid.json()["requested_language"] == "en" and invalid.json()["answer"] == english.json()["answer"]
