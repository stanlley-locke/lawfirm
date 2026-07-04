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


def test_bootstrap_initial_admin_creates_first_admin(app, monkeypatch):
    monkeypatch.setenv('ADMIN_USERNAME', 'bootstrap-admin')
    monkeypatch.setenv('ADMIN_EMAIL', 'bootstrap@example.com')
    monkeypatch.setenv('ADMIN_PASSWORD', 'bootstrap-pass-123')

    from app import bootstrap_initial_admin
    from models import User
    from extensions import db

    with app.app_context():
        User.query.delete()
        db.session.commit()

        bootstrap_initial_admin()

        admin = User.query.filter_by(username='bootstrap-admin').first()
        assert admin is not None
        assert admin.email == 'bootstrap@example.com'
        assert admin.is_admin is True
        assert admin.check_password('bootstrap-pass-123')


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


def test_login_rate_limiting(client):
    for _ in range(5):
        response = client.post('/auth/login', data={'username': 'admin', 'password': 'wrong'})
        assert response.status_code in (200, 302)
    response = client.post('/auth/login', data={'username': 'admin', 'password': 'wrong'})
    assert response.status_code == 200


def test_public_case_tracker(client, app):
    from models import LegalCase, User
    from extensions import db
    
    with app.app_context():
        c = User(username='testclient', email='client@test.com', is_admin=False)
        c.set_password('pass123')
        db.session.add(c)
        db.session.commit()
        
        case = LegalCase(
            case_number='TEST-001',
            title='Test Conveyancing Matter',
            client_id=c.id,
            case_type='Land Law',
            status='Active',
            reference_code='TESTREF123'
        )
        db.session.add(case)
        db.session.commit()
        
    response = client.get('/track-case?code=TESTREF123')
    assert response.status_code == 200
    assert b'Test Conveyancing Matter' in response.data
    
    response = client.get('/track-case?code=INVALID')
    assert response.status_code == 200
    assert b'No case found with that Reference Code' in response.data


def test_client_portal_login_and_dashboard(client, app):
    from models import User
    from extensions import db
    
    with app.app_context():
        c = User(username='testclient2', email='client2@test.com', is_admin=False)
        c.set_password('pass123')
        db.session.add(c)
        db.session.commit()
        
    response = client.post('/client/login', data={'username': 'testclient2', 'password': 'pass123'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'matters' in response.data or b'Matters' in response.data or b'Client Dashboard' in response.data


def test_document_generator(admin_client):
    response = admin_client.post('/admin/generate-document', data={
        'template_type': 'nda',
        'disclosing_party': 'Disclosing Inc',
        'receiving_party': 'Receiving Corp',
        'purpose': 'Evaluation',
        'agreement_date': '2026-07-04'
    })
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/pdf'
    assert b'%PDF' in response.data


def test_quick_reply_message(admin_client, app):
    from models import ContactMessage
    from extensions import db
    import io
    
    with app.app_context():
        msg = ContactMessage(
            name='Test Sender',
            email='sender@test.com',
            subject='Question about land law',
            message='Can you help me buy land?',
            is_read=False
        )
        db.session.add(msg)
        db.session.commit()
        msg_id = msg.id
        
    data = {
        'body': 'Yes, we can help you buy land. Please find attached documents.',
        'attachments': (io.BytesIO(b'Mock file contents here'), 'test_doc.txt')
    }
    response = admin_client.post(f'/admin/messages/{msg_id}/quick-reply', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    assert response.json == {'success': True}
    
    with app.app_context():
        msg_after = ContactMessage.query.get(msg_id)
        assert msg_after.is_read is True


def test_reopen_and_delete_chat(admin_client, app):
    from models import ChatRoom, ChatMessage
    from extensions import db
    
    with app.app_context():
        room = ChatRoom(
            room_id='test-room-123',
            client_name='Test Client',
            is_active=False
        )
        db.session.add(room)
        
        msg = ChatMessage(
            room='test-room-123',
            client_name='Test Client',
            content='Hello',
            is_from_client=True
        )
        db.session.add(msg)
        db.session.commit()
        
    # Reopen room
    response = admin_client.post('/admin/chat/test-room-123/reopen')
    assert response.status_code == 200
    assert response.json == {'success': True}
    
    with app.app_context():
        room_after = ChatRoom.query.filter_by(room_id='test-room-123').first()
        assert room_after.is_active is True
        
    # Delete room
    response = admin_client.post('/admin/chat/test-room-123/delete')
    assert response.status_code == 200
    assert response.json == {'success': True}
    
    with app.app_context():
        room_del = ChatRoom.query.filter_by(room_id='test-room-123').first()
        assert room_del is None
        msg_del = ChatMessage.query.filter_by(room='test-room-123').first()
        assert msg_del is None


def test_chat_extra_features(admin_client, app):
    from models import CannedResponse, ChatSetting
    from extensions import db
    
    # 1. Test chat settings saving
    response = admin_client.post('/admin/chat/settings', json={
        'business_hours_start': '10',
        'business_hours_end': '16',
        'business_hours_days': '1,2,3',
        'closed_message': 'Sorry we are out'
    })
    assert response.status_code == 200
    assert response.json == {'success': True}
    
    with app.app_context():
        start_set = ChatSetting.query.filter_by(key='business_hours_start').first()
        assert start_set.value == '10'
        
    # 2. Test saving a canned response
    response = admin_client.post('/admin/chat/canned', data={
        'shortcut': '/hello',
        'content': 'Hello from team'
    })
    assert response.status_code == 200
    assert response.json == {'success': True}
    
    with app.app_context():
        canned = CannedResponse.query.filter_by(shortcut='/hello').first()
        assert canned is not None
        assert canned.content == 'Hello from team'
        canned_id = canned.id
        
    # 3. Test deleting a canned response
    response = admin_client.post(f'/admin/chat/canned/{canned_id}/delete')
    assert response.status_code == 200
    assert response.json == {'success': True}
    
    with app.app_context():
        canned_del = CannedResponse.query.get(canned_id)
        assert canned_del is None


def test_admin_chats_page_with_anonymous_client(admin_client, app):
    from models import ChatRoom
    from extensions import db
    
    with app.app_context():
        room = ChatRoom(
            room_id='anon-room-999',
            client_name=None,
            is_active=True
        )
        db.session.add(room)
        db.session.commit()
        
    response = admin_client.get('/admin/chats')
    assert response.status_code == 200
    assert b'Anonymous' in response.data


def test_chat_start_notifications(client, app):
    from models import ChatMessage, ChatSetting
    from extensions import db

    with app.app_context():
        ChatSetting.query.delete()
        db.session.commit()

    response = client.post('/chat/start', json={
        'name': 'Visitor Two',
        'email': 'visitor@test.com'
    })
    assert response.status_code == 200
    room_id = response.json['room_id']

    with app.app_context():
        msgs = ChatMessage.query.filter_by(room=room_id).all()
        assert len(msgs) > 0
        content = msgs[0].content
        assert ("office is currently closed" in content) or ("advocates are currently away" in content)

def test_admin_impersonate_client(admin_client, client, app):
    from models import User
    from extensions import db

    with app.app_context():
        client_user = User(username='testclient', email='client@test.com')
        client_user.set_password('password123')
        client_user.is_admin = False
        db.session.add(client_user)
        db.session.commit()
        client_id = client_user.id

    response = admin_client.post(f'/admin/users/impersonate/{client_id}', follow_redirects=True)
    assert response.status_code == 200
    assert b'Logged in as testclient' in response.data

    response = admin_client.post('/client/stop-impersonation', follow_redirects=True)
    assert response.status_code == 200
    assert b'Switched back to Administrator' in response.data


