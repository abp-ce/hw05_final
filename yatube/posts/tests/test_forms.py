import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
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
            text='Тестовая пост',
            group=cls.group,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост 2',
            'group': PostFormTests.group.pk
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': PostFormTests.user.username}
        ))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.filter(text=form_data['text']).get()
        self.assertEqual(post.author, PostFormTests.user)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group, PostFormTests.group)

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        group = Group.objects.create(
            title='Тестовая группа 1',
            slug='test-slug1',
            description='Тестовое описание',
        )
        form_data = {
            'text': 'Тестовый пост 3',
            'group': group.pk
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=(PostFormTests.post.pk,)),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            args=(PostFormTests.post.pk,)
        ))
        post = Post.objects.filter(text=form_data['text']).get()
        self.assertEqual(post.author, PostFormTests.user)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group, group)

    def test_add_comment(self):
        """После успешной отправки комментарий появляется на странице поста."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=(PostFormTests.post.pk,)),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertContains(response, form_data['text'])
