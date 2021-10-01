from tests.conftest import admin_login, login, logout


def test_empty_db(client):
    rv = client.get("/")
    assert rv.status_code == 302


def test_login_logout_admin(app, client):
    """Make sure login and logout works."""

    rv = login(client, "admin", app.config["ADMIN_PASSWORD"])
    assert rv.status_code == 200

    rv = logout(client)
    assert rv.status_code == 200


def test_login_logout_user(client):
    rv = login(client, "test@test.com", "test")
    assert rv.status_code == 200

    rv = logout(client)
    assert rv.status_code == 200


def test_login_logout_bad_user(client):
    rv = login(client, f"adminx", "admin")
    assert rv.status_code == 403


def test_login_logout_bad_password(client):
    rv = login(client, "admin", "not_correct_password")
    assert rv.status_code == 403


def test_upload_record(client):
    """Test adding a sample roster and parsing"""
    rv = login(client, "admin", "admin")
    assert rv.status_code == 200

    data = {}

    rv = client.post(
        "/upload_record",
        data=data,
        follow_redirects=True,
        content_type="multipart/form-data",
    )
    assert b"Missing file" in rv.data

    data["record"] = (b"", "")
    rv = client.post(
        "/upload_record",
        data=data,
        follow_redirects=True,
        content_type="multipart/form-data",
    )
    assert b"No selected file" in rv.data

    data["record"] = (b"", "foo")
    rv = client.post(
        "/upload_record",
        data=data,
        follow_redirects=True,
        content_type="multipart/form-data",
    )
    assert b"Wrong filetype, convert to CSV please" in rv.data

    with open("tests/test_roster.csv", "rb") as roster_file:
        data["record"] = (roster_file, "roster.csv")
        rv = client.post(
            "/upload_record",
            data=data,
            follow_redirects=True,
            content_type="multipart/form-data",
        )

        assert rv.status_code == 200
        assert b"New workers: 10" in rv.data
        assert b"Burrito,Frozen Bean" in rv.data
        assert b"Anthropology Dept" in rv.data

    rv = client.get("/worker/1")

    assert b'placeholder="gender is a spectrum"' in rv.data
    assert b'placeholder="worker@private.email"' in rv.data
    assert b'placeholder="(808) 123-4567"' in rv.data

    assert b"Station,International Space" in rv.data
    assert b'value="Curriculum Studies" disabled />' in rv.data
    assert b'id="active" checked>' in rv.data

    rv = client.get("/upload_record")
    assert b"Found 10 new workers" in rv.data


# def test_add_worker(app, client):
#    """xXx"""
#    rv = login(client, "admin", app.config["ADMIN_PASSWORD"])
#    assert rv.status_code == 200
#
#    data = dict(
#        name="Test,Worker",
#        contract="manual",
#        department_id=0,
#        organizing_dept=0,
#        updated=date.today(),
#        unit=0,
#        preferred_name="Worka",
#        pronouns="he/him",
#        email="test@worker.com",
#        notes="These are notes",
#        active=True,
#    )
#
#    rv = client.post("/worker/", data=data, follow_redirects=True)
#    print(rv.data)
#    assert rv.status_code == 200
