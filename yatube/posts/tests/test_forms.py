import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Mr.X')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Новый пост',
            'group': self.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post = Post.objects.last()
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.image, f'posts/{uploaded}')

    def test_edit_post(self):
        """Проверка редактирования поста."""
        post = Post.objects.create(
            author=self.user,
            text='Тестовый текст для поста!',
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Пост id=1 отредактирован',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )
        post.refresh_from_db()
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': post.id}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.author, self.user)

    def test_edit_post_no_author(self):
        """Проверка редактирования поста не автором."""
        authorized_client_no_author = User.objects.create_user(
            username='Mr.Y'
        )
        self.authorized_client_no_author = Client()
        self.authorized_client_no_author.force_login(
            authorized_client_no_author
        )
        post = Post.objects.create(
            author=self.user,
            text='Тестовый текст для поста!',
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Пост id=1 отредактирован',
            'group': self.group.id,
        }
        response = self.authorized_client_no_author.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )
        post.refresh_from_db()
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': post.id}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertNotEqual(post.text, form_data['text'])
        self.assertIsNone(post.group)

    def test_create_post_not_authorized(self):
        """Проверка попытки создания записи в Post."""
        rev_login = reverse('users:login')
        rev_create = reverse('posts:post_create')
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый пост',
            'group': self.group.id,
        }
        response = self.client.post(
            rev_create,
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(
            response, f'{rev_login}?next={rev_create}'
        )

    def test_create_comment(self):
        """Валидная форма создает комментарий к посту."""
        comment_count = Comment.objects.count()
        post = Post.objects.create(
            author=self.user,
            text='Тестовый текст для поста!',
        )
        form_data = {
            'post': post,
            'text': 'Новый коментарий',
            'author': self.user,
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )
        comment = Comment.objects.last()
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': post.id}))
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.user)

    def test_create_comment_not_authorized(self):
        """Проверка попытки создания записи комментария."""
        comment_count = Comment.objects.count()
        post = Post.objects.create(
            author=self.user,
            text='Тестовый текст для поста!',
        )
        form_data = {
            'post': post,
            'text': 'Новый коментарий',
            'author': self.user,
        }
        response = self.client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )
        rev_login = reverse('users:login')
        rev_comment = reverse('posts:add_comment', kwargs={'post_id': post.id})
        self.assertEqual(Comment.objects.count(), comment_count)
        self.assertRedirects(
            response, f'{rev_login}?next={rev_comment}'
        )
