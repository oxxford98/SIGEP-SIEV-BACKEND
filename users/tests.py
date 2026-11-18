from rest_framework.test import APITestCase

from users.models import User

FRONT_ORIGIN = 'http://localhost:5173'


class AuthFlowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin', email='admin@siev.test', password='Clave12345!', is_staff=True
        )

    def login(self, email='admin@siev.test', password='Clave12345!'):
        return self.client.post('/api/auth/login', {'email': email, 'password': password}, format='json')

    def test_cors_preflight_allows_frontend(self):
        response = self.client.options(
            '/api/auth/login',
            HTTP_ORIGIN=FRONT_ORIGIN,
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS='authorization,content-type',
        )
        self.assertEqual(response.headers.get('Access-Control-Allow-Origin'), FRONT_ORIGIN)
        self.assertIn('authorization', response.headers.get('Access-Control-Allow-Headers', ''))

    def test_cors_rejects_unknown_origin(self):
        response = self.client.options(
            '/api/auth/login', HTTP_ORIGIN='http://evil.test', HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST'
        )
        self.assertNotIn('Access-Control-Allow-Origin', response.headers)

    def test_login_returns_tokens_and_me_returns_user(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertIn('refresh', response.data)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        me = self.client.get('/api/user/me/')
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data['email'], 'admin@siev.test')
        self.assertTrue(me.data['is_staff'])
        self.assertNotIn('password', me.data)

    def test_me_requires_token(self):
        self.assertEqual(self.client.get('/api/user/me/').status_code, 401)

    def test_wrong_password_is_rejected(self):
        self.assertEqual(self.login(password='otra').status_code, 401)

    def test_public_register_cannot_grant_privileges(self):
        response = self.client.post('/api/user/', {
            'username': 'nuevo', 'email': 'nuevo@siev.test', 'password': 'Clave12345!',
            'is_staff': True, 'is_superuser': True,
        }, format='json')
        self.assertEqual(response.status_code, 201)
        created = User.objects.get(email='nuevo@siev.test')
        self.assertFalse(created.is_staff)
        self.assertFalse(created.is_superuser)
        self.assertEqual(self.login('nuevo@siev.test').status_code, 200)

    def test_list_and_soft_delete(self):
        other = User.objects.create_user(username='otro', email='otro@siev.test', password='Clave12345!')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.login().data['access']}")

        self.assertEqual(self.client.get('/api/user/').status_code, 200)
        self.assertEqual(self.client.delete(f'/api/user/{other.id}/').status_code, 200)

        emails = [u['email'] for u in self.client.get('/api/user/').data]
        self.assertNotIn('otro@siev.test', emails)
        self.assertEqual(self.login('otro@siev.test').status_code, 401)
