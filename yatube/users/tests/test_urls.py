from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class UserURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.authorized = (
            '/auth/password_change/',
            '/auth/password_change/done/',
            '/auth/logout/',
        )
        guest = (
            '/auth/signup/',
            '/auth/login/',
            '/auth/password_reset/',
            '/auth/password_reset/done/',
            '/auth/reset/NA/5z1-131f74940a0a25cee359/',
            '/auth/reset/done/',
        )
        template = (
            'users/signup.html',
            'users/login.html',
            'users/password_reset_form.html',
            'users/password_reset_done.html',
            'users/password_reset_confirm.html',
            'users/password_reset_complete.html',
            'users/password_change_form.html',
            'users/password_change_done.html',
            'users/logged_out.html'
        )
        super().setUpClass()
        cls.url_templates_names = tuple(
            zip(guest + cls.authorized, template)
        )
        cls.user = User.objects.create_user(username='auth')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(UserURLTests.user)

    def test_urls_exist_and_use_right_template_at_desired_location(self):
        """Страница доступна пользователю и использует правильный шаблон."""
        for url, template in UserURLTests.url_templates_names:
            with self.subTest(url=url):
                client = (
                    self.authorized_client if url in UserURLTests.authorized
                    else self.guest_client
                )
                response = client.get(url, follow=True)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)
