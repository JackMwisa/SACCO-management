from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages

User = get_user_model()

class AuthViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_password = 'StrongPass123'
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password=self.user_password
        )

    def test_register_view_get(self):
        response = self.client.get(reverse('user_auths:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_auths/register.html')

    def test_register_view_post_success(self):
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'TestPass456!',
            'password2': 'TestPass456!',
        }
        response = self.client.post(reverse('user_auths:register'), data, follow=True)
        self.assertRedirects(response, reverse('account:account'))
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_login_view_get(self):
        response = self.client.get(reverse('user_auths:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_auths/login.html')

    def test_login_view_post_valid(self):
        response = self.client.post(reverse('user_auths:login'), {
            'email': self.user.email,
            'password': self.user_password,
        }, follow=True)
        self.assertRedirects(response, reverse('account:account'))
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("You are logged.", str(messages[0]))

    def test_login_view_post_invalid_password(self):
        response = self.client.post(reverse('user_auths:login'), {
            'email': self.user.email,
            'password': 'wrongpass',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Username or password does not exist", response.content.decode())

    def test_login_view_post_nonexistent_user(self):
        response = self.client.post(reverse('user_auths:login'), {
            'email': 'doesnotexist@example.com',
            'password': 'pass',
        }, follow=True)
        self.assertIn("User does not exist", response.content.decode())

    def test_logout_view(self):
        self.client.login(email=self.user.email, password=self.user_password)
        response = self.client.get(reverse('user_auths:logout'), follow=True)
        self.assertRedirects(response, reverse('user_auths:login'))
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("You have been logged out", str(messages[0]))

    def test_logout_admin_redirect(self):
        self.client.login(email=self.user.email, password=self.user_password)
        response = self.client.get(reverse('user_auths:logout_admin'), follow=True)
        self.assertRedirects(response, "/admin/login/")
