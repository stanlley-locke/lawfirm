def test_health_endpoint(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'


def test_homepage(client):
    response = client.get('/')
    assert response.status_code == 200


def test_contact_form_get(client):
    response = client.get('/contact')
    assert response.status_code == 200


def test_login_invalid(client):
    response = client.post('/auth/login', data={'username': 'admin', 'password': 'wrong'})
    assert response.status_code in (200, 302)


def test_admin_dashboard_requires_auth(client):
    response = client.get('/admin/')
    assert response.status_code == 302


def test_admin_dashboard_with_auth(admin_client):
    response = admin_client.get('/admin/')
    assert response.status_code == 200


def test_token_access_removed(client):
    response = client.get('/auth/token-access/fake-token')
    assert response.status_code == 404


def test_secret_login_removed(client):
    response = client.get('/auth/secret')
    assert response.status_code == 404


def test_privacy_page(client):
    response = client.get('/privacy')
    assert response.status_code == 200


def test_search_page(client):
    response = client.get('/search?q=law')
    assert response.status_code == 200


def test_chat_page(client):
    response = client.get('/chat')
    assert response.status_code == 200
