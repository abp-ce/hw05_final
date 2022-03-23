from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Follow, Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
        )
        cls.templates_url_names = (
            ('/', 'posts/index.html',),
            (f'/group/{PostURLTests.group.slug}/', 'posts/group_list.html',),
            (f'/profile/{PostURLTests.user.username}/', 'posts/profile.html',),
            (f'/posts/{PostURLTests.post.pk}/', 'posts/post_detail.html',),
            (
                f'/posts/{PostURLTests.post.pk}/edit/',
                'posts/create_post.html',
            ),
            ('/create/', 'posts/create_post.html',),
        )
        cls.authorized = ('/create/', f'/posts/{PostURLTests.post.pk}/edit/',)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)

    def test_urls_exist_at_desired_location(self):
        """Страница доступна пользователю."""
        for url, _ in PostURLTests.templates_url_names:
            with self.subTest(url=url):
                client = (self.authorized_client
                          if url in PostURLTests.authorized
                          else self.guest_client)
                response = client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_exist_and_use_right_template_at_desired_location(self):
        """Страница использует правильный шаблон."""
        for url, template in PostURLTests.templates_url_names:
            with self.subTest(url=url):
                client = (self.authorized_client
                          if url in PostURLTests.authorized
                          else self.guest_client)
                response = client.get(url)
                self.assertTemplateUsed(response, template)

    def test_unexisting_url(self):
        """Тест не существующей страницы"""
        response = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_edit_url_redirect_anonymous_and_non_author(self):
        """Страница /post_edit/ перенаправляет анонимного пользователя."""
        response = self.guest_client.get(
            f'/posts/{PostURLTests.post.pk}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response,
            '/auth/login/?next='f'/posts/{PostURLTests.post.pk}/edit/'
        )
        user = User.objects.create_user(username='another_auth')
        another_client = Client()
        another_client.force_login(user)
        response = another_client.get(f'/posts/{PostURLTests.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response, f'/posts/{PostURLTests.post.pk}/'
        )

    def test_create_url_redirect_anonymous(self):
        """Страница /create/ перенаправляет анонимного пользователя."""
        response = self.guest_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response,
            '/auth/login/?next=/create/'
        )

    def test_add_comment_only_authorized(self):
        """Не авторизованный пользователь не может доавить комментарий."""
        response = self.guest_client.get(f'/posts/{PostURLTests.post.pk}/')
        self.assertNotContains(response, 'Добавить комментарий:')

    def test_authorized_can_add_delete_subscription(self):
        """
        Авторизованный пользователь может подписываться на 
        других пользователей и удалять их из подписок.
        """
        user = User.objects.create_user(username='another')
        response = self.authorized_client.get(f'/profile/{user.username}/follow/')
        self.assertRedirects(response, f'/profile/{user.username}/')
        response = self.authorized_client.get(f'/profile/{user.username}/unfollow/')
        self.assertRedirects(response, f'/profile/{user.username}/')
        user.delete()

    def test_new_post_appear_to_followers_only(self):
        """
        Новая запись пользователя появляется в ленте тех, кто на него подписан
        и не появляется в ленте тех, кто не подписан.
        """
        user = User.objects.create_user(username='user')
        follower_user = User.objects.create_user(username='follower_user')
        post = Post.objects.create(
            author=PostURLTests.user,
            text='Тестовый пост 22',
        )
        subscription = Follow.objects.create(
            user=follower_user,
            author=PostURLTests.user
        )
        self.user_client = Client()
        self.user_client.force_login(user)
        response = self.user_client.get('/follow/')
        self.assertNotContains(response, post.text)
        self.user_client.force_login(follower_user)
        response = self.user_client.get('/follow/')
        self.assertContains(response, post.text)
        user.delete()
        follower_user.delete()
        post.delete()
        subscription.delete()
