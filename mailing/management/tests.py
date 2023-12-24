from django.test import TestCase
from django.contrib.auth.models import User


class TestPaths(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='test', password='test')
    def test_path_index(self):
        response = self.client.get('')
        self.assertEquals(response.status_code, 200)

    def test_path_index_anonymous_user(self):
        response = self.client.get('')
        # self.mailing_client = Client.objects.create(phone_number='79876543211', tag='aaqqqa')
        self.assertIn('Авторизация', response.content.decode())

    def test_path_index_auth_admin(self):
        self.client.login(username='test', password='test')
        response = self.client.get('')
        self.assertIn('Выйти', response.content.decode())

    def test_path_admin_panel_anonymous_user(self):
        response = self.client.get('/admin/')
        self.assertEquals(response.status_code, 302)

    def test_path_admin_panel_auth_admin(self):
        self.client.login(username='test', password='test')
        response = self.client.get('/admin/')
        self.assertEquals(response.status_code, 200)

    def test_path_api_client_anonymous_user(self):
        response = self.client.get('/api/v1/client/')
        self.assertIn('Учетные данные не были предоставлены.', response.content.decode())

    def test_path_api_client_auth_admin(self):
        self.client.login(username='test', password='test')
        response = self.client.get('/api/v1/client/')
        self.assertNotIn('Учетные данные не были предоставлены.', response.content.decode())
        self.assertEquals(response.status_code, 200)

    def test_path_api_message_anonymous_user(self):
        response = self.client.get('/api/v1/message/')
        self.assertIn('Учетные данные не были предоставлены.', response.content.decode())

    def test_path_api_message_auth_admin(self):
        self.client.login(username='test', password='test')
        response = self.client.get('/api/v1/message/')
        self.assertNotIn('Учетные данные не были предоставлены.', response.content.decode())
        self.assertEquals(response.status_code, 200)

    def test_path_api_mailing_anonymous_user(self):
        response = self.client.get('/api/v1/mailing/')
        self.assertIn('Учетные данные не были предоставлены.', response.content.decode())

    def test_path_api_mailing_auth_admin(self):
        self.client.login(username='test', password='test')
        response = self.client.get('/api/v1/mailing/')
        self.assertNotIn('Учетные данные не были предоставлены.', response.content.decode())
        self.assertEquals(response.status_code, 200)
