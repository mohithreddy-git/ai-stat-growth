def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_employee_login_and_me(client):
    response = client.post("/api/auth/login", json={"email": "employee.demo@aistatgrowth.gov.in", "password": "Demo@123"})
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["full_name"] == "Dr. Ananya Sharma"
    assert body["user"]["role"] == "EMPLOYEE"

    me = client.get("/api/users/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["employee_id"] == "EMP-0001"


def test_invalid_login_is_rejected(client):
    response = client.post("/api/auth/login", json={"email": "employee.demo@aistatgrowth.gov.in", "password": "wrong"})
    assert response.status_code == 401


def test_admin_route_is_role_protected(client):
    employee = client.post("/api/auth/login", json={"email": "employee.demo@aistatgrowth.gov.in", "password": "Demo@123"}).json()
    admin = client.post("/api/auth/login", json={"email": "admin.demo@aistatgrowth.gov.in", "password": "Demo@123"}).json()
    employee_check = client.get("/api/admin/access-check", headers={"Authorization": f"Bearer {employee['access_token']}"})
    admin_check = client.get("/api/admin/access-check", headers={"Authorization": f"Bearer {admin['access_token']}"})
    assert employee_check.status_code == 403
    assert admin_check.status_code == 200


def test_bootstrap_has_seeded_foundation(client):
    login = client.post("/api/auth/login", json={"email": "trainer.demo@aistatgrowth.gov.in", "password": "Demo@123"}).json()
    response = client.get("/api/bootstrap", headers={"Authorization": f"Bearer {login['access_token']}"})
    assert response.status_code == 200
    counts = response.json()["seeded_counts"]
    assert counts["users"] == 50
    assert counts["departments"] == 5
    assert counts["competencies"] >= 25
    assert counts["courses"] >= 30
    assert counts["training_programmes"] >= 15
