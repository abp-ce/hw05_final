import shutil
import tempfile
import time

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Page
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded
        )
        cls.templates_pages_names = (
            ('posts:index', 'posts/index.html', tuple()),
            ('posts:group_list', 'posts/group_list.html',
             (PostViewTests.group.slug,)),
            ('posts:profile', 'posts/profile.html',
             (PostViewTests.user.username,)),
            ('posts:post_detail', 'posts/post_detail.html',
             (PostViewTests.post.pk,)),
            ('posts:post_edit', 'posts/create_post.html',
             (PostViewTests.post.pk,)),
            ('posts:post_create', 'posts/create_post.html', tuple()),
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def post_test(self, response):
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewTests.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = PostViewTests.templates_pages_names
        for reverse_name, template, args in templates_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse(reverse_name,
                                                      args=args))
                self.assertTemplateUsed(response, template)

    def test_index_and_group_list_and_profile_pages_paginations(self):
        """Тест работы паджинации на шаблонах index, group_list и profile."""
        POSTS_NUM = 13
        POSTS_ON_PAGE = 10
        posts = [Post(author=PostViewTests.user,
                      text=f'Тестовый пост {i}',
                      group=PostViewTests.group) for i in range(POSTS_NUM)]
        Post.objects.bulk_create(posts)
        names = ('posts:index', 'posts:group_list', 'posts:profile')
        templates_pages_names = PostViewTests.templates_pages_names
        for reverse_name, _, args in templates_pages_names:
            if reverse_name in names:
                with self.subTest(reverse_name=reverse_name):
                    response = self.authorized_client.get(
                        reverse(reverse_name, args=args)
                    )
                    self.assertEqual(
                        len(response.context['page_obj']), POSTS_ON_PAGE
                    )
                    response = self.authorized_client.get(
                        reverse(reverse_name, args=args) + '?page=2'
                    )
                    self.assertEqual(len(response.context['page_obj']),
                                     POSTS_NUM - POSTS_ON_PAGE + 1)

    def test_index_pages_show_correct_context_and_right_pic(self):
        """Шаблон index сформирован с правильным контекстом и картинкой."""
        response = (
            self.authorized_client.
            get(reverse('posts:index'))
        )
        self.assertIsInstance(response.context.get('page_obj'), Page)
        self.assertEqual(
            response.context.get('page_obj')[0].image,
            PostViewTests.post.image
        )

    def test_group_list_pages_show_correct_contextand_right_pic(self):
        """
        Шаблон group_list сформирован с правильным контекстом и картинкой.
        """
        response = (
            self.authorized_client.
            get(reverse('posts:group_list',
                        kwargs={'slug': PostViewTests.group.slug}))
        )
        self.assertIsInstance(response.context.get('group'), Group)
        self.assertIsInstance(response.context.get('page_obj'), Page)
        self.assertEqual(
            response.context.get('page_obj')[0].image,
            PostViewTests.post.image
        )

    def test_profile_pages_show_correct_context_and_right_pic(self):
        """
        Шаблон profile сформирован с правильным контекстом и картинкой.
        """
        response = (
            self.authorized_client.
            get(reverse('posts:profile',
                        kwargs={'username': PostViewTests.user.username}))
        )
        self.assertIsInstance(response.context.get('author'), User)
        self.assertEqual(response.context.get('count'),
                         Post.objects.count())
        self.assertIsInstance(response.context.get('page_obj'), Page)
        self.assertEqual(
            response.context.get('page_obj')[0].image,
            PostViewTests.post.image
        )

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (
            self.authorized_client.
            get(reverse('posts:post_detail',
                        kwargs={'post_id': PostViewTests.post.pk}))
        )
        self.assertEqual(response.context.get('post'), PostViewTests.post)
        self.assertEqual(response.context.get('title'),
                         PostViewTests.post.text[:30])
        self.assertEqual(response.context.get('author'), PostViewTests.user)
        self.assertEqual(response.context.get('count'),
                         Post.objects.count())

    def test_post_edit_pages_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = (
            self.authorized_client.
            get(reverse('posts:post_edit',
                        kwargs={'post_id': PostViewTests.post.pk}))
        )
        self.post_test(response)
        self.assertEqual(response.context.get('is_edit'), True)

    def test_create_post_pages_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = (
            self.authorized_client.
            get(reverse('posts:post_create'))
        )
        self.post_test(response)

    def test_create_post_with_group_appears_in_right_pages(self):
        """Пост с группой появляется на нужных страницах."""
        CACHE_TIME = 20
        group = Group.objects.create(
            title='Тестовая группа 1',
            slug='test-slug1',
            description='Тестовое описание 1',
        )
        post = Post.objects.create(
            author=PostViewTests.user,
            text='Тестовая пост 100',
            group=group
        )
        time.sleep(CACHE_TIME)
        response = (
            self.guest_client.
            get(reverse('posts:index'))
        )
        self.assertContains(response, post.text)
        response = (
            self.guest_client.
            get(reverse('posts:group_list',
                        kwargs={'slug': group.slug}))
        )
        response = (
            self.guest_client.
            get(reverse('posts:group_list',
                        kwargs={'slug': PostViewTests.group.slug}))
        )
        self.assertNotContains(response, 'Тестовая пост 100')
        response = (
            self.guest_client.
            get(reverse('posts:profile',
                        kwargs={'username': PostViewTests.user.username}))
        )
        self.assertContains(response, post.text)

    def test_cache_index_page(self):
        """Проверка кеширования главной страницы."""
        CACHE_TIME = 20
        post = Post.objects.create(
            author=PostViewTests.user,
            text='Тестовый пост 55',
        )
        response = self.guest_client.get(reverse('posts:index'))
        self.assertNotContains(response, post.text)
        time.sleep(CACHE_TIME)
        response = self.guest_client.get(reverse('posts:index'))
        self.assertContains(response, post.text)
        post.delete()
        response = self.guest_client.get(reverse('posts:index'))
        self.assertContains(response, post.text)
        time.sleep(CACHE_TIME)
        response = self.guest_client.get(reverse('posts:index'))
        self.assertNotContains(response, post.text)
