from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from http import HTTPStatus
from posts.models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Mr.X')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст!!!!!!!!!!!',
        )

    def setUp(self):
        # Создаем авторизованый клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_guest_client(self):
        """Проверка доступности страниц для всех пользователей."""
        templates_url_names = (
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.id}/',
        )
        for address in templates_url_names:
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_reverse_name(self):
        reverse_name_urls = (
            ('posts:index', None, '/'),
            ('posts:group_posts', (self.group.slug,),
                f'/group/{self.group.slug}/'),
            ('posts:profile', (self.user.username,),
                f'/profile/{self.user.username}/'),
            ('posts:post_detail', (self.post.id,), f'/posts/{self.post.id}/'),
            ('posts:post_edit', (self.post.id,),
                f'/posts/{self.post.id}/edit/'),
            ('posts:post_create', None, '/create/')
        )
        for name, args, link in reverse_name_urls:
            with self.subTest(name=name):
                self.assertEqual(reverse(name, args=args), link)

    def test_urls_uses_authorized_client(self):
        """Проверка доступности страниц

        Проверяет страницы /create/ и /edit/
        для авторизованого пользователя автора поста.
        """
        urls = {
            reverse('posts:post_create'),
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            ),
        }
        for reverse_name in urls:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_create_page(self):
        """Проверка доступности страницы /create/

        Проверяет доступность страницы /create/ для неавторизованого
        пользователя и перенаправление на страницу /login/.
        """
        response = self.client.get(
            reverse('posts:post_create'), follow=True
        )
        self.assertRedirects(response, ('/auth/login/?next=/create/'))

    def test_urls_uses_correct_edit_authorized_client_no_author(self):
        """Проверка доступности страницы /edit/

        Проверяет доступность страницы /edit/
        если обращается не автор поста.
        """
        authorized_client_no_author = User.objects.create_user(
            username='Mr.Y')
        self.authorized_client_no_author = Client()
        self.authorized_client_no_author.force_login(
            authorized_client_no_author)
        response = self.authorized_client_no_author.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )

    def test_urls_uses_correct_unexisting_page(self):
        """Страница /unexisting_page/ не существует."""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
