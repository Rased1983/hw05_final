import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Follow, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Mr.X')
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
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст для поста!',
            group=cls.group,
            image=uploaded,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """Namespace использует соответствующий шаблон."""
        templates_page_names = (
            ('index', None, 'index.html'),
            ('group_posts', (self.group.slug,), 'group_list.html'),
            ('profile', (self.user.username,), 'profile.html'),
            ('post_detail', (self.post.id,), 'post_detail.html'),
            ('post_edit', (self.post.id,), 'post_create.html'),
            ('post_create', None, 'post_create.html')
        )
        cache.clear()
        for name, args, template in templates_page_names:
            with self.subTest(name=name):
                response = self.authorized_client.get(
                    reverse(f'posts:{name}', args=args)
                )
                self.assertTemplateUsed(response, f'posts/{template}')

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        self.check_post(response, is_page=True)

    def test_group_page_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:group_posts', kwargs={'slug': self.group.slug})
        )
        self.assertIsNotNone(response)
        self.check_post(response, is_page=True)
        self.assertIn('group', response.context)
        object_group = response.context['group']
        post_group_title = object_group.title
        post_group_description = object_group.description
        self.assertEqual(post_group_title, self.post.group.title)
        self.assertEqual(post_group_description, self.post.group.description)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        self.assertIsNotNone(response)
        self.check_post(response, is_page=True)
        self.assertIn('author', response.context)
        object_author = response.context['author']
        self.assertEqual(object_author, self.user)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertIsNotNone(response)
        self.check_post(response, is_page=False)

    def test_post_create_show_correct_context(self):
        """Проверка формы в шаблоне create и edit."""
        address = (
            ('posts:post_create', None),
            ('posts:post_edit', [self.post.id]),
        )
        for name, args in address:
            with self.subTest(name=name):
                response = self.authorized_client.get(reverse(name, args=args))
                self.assertIsNotNone(response)
                self.assertIn('form', response.context)
                form_field = response.context['form']
                self.assertIsInstance(form_field, PostForm)

    def check_post(self, response, is_page):
        if is_page:
            self.assertIn('page_obj', response.context)
            self.assertNotEqual(len(response.context['page_obj']), 0)
            post = response.context['page_obj'][0]
        else:
            self.assertIn('post', response.context)
            post = response.context['post']
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertEqual(post.image, self.post.image)


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Mr.X')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        blogs = []
        cls.number_posts = settings.PAGINATOR_PAGE + 3
        for post_num in range(cls.number_posts):
            blogs.append(Post(
                author=cls.user,
                text='Пост №%s!' % post_num,
                group=cls.group)
            )
        Post.objects.bulk_create(blogs)

    def test_first_page_contains_correct_records(self):
        """Проверка что на первой странице выведено PAGINATOR_PAGE постов."""
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(
            len(response.context['page_obj']), settings.PAGINATOR_PAGE
        )

    def test_second_page_contains_correct_records(self):
        """Проверка второй страницы паджинатора."""
        page, posts = divmod(self.number_posts, settings.PAGINATOR_PAGE)
        if page >= 2:
            posts_number = settings.PAGINATOR_PAGE
        else:
            posts_number = posts
        response = self.client.get(reverse('posts:index'), {'page': '2'})
        self.assertEqual(
            len(response.context['page_obj']), posts_number)


class PostCreateTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Mr.X')
        cls.group_1 = Group.objects.create(
            title='Тестовая группа 1',
            slug='test-slug_1',
            description='Тестовое описание группы 1',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug_2',
            description='Тестовое описание группы 2',
        )
        cls.post_1 = Post.objects.create(
            author=cls.user,
            text='Тестовый текст для поста 1!',
            group=cls.group_1
        )
        cls.page_name = {
            reverse('posts:index'),
            reverse(
                'posts:group_posts', kwargs={'slug': cls.group_1.slug}
            ),
            reverse(
                'posts:profile', kwargs={'username': cls.user.username}
            ),
        }

    def test_post_create_contains_index_and_etc(self):
        """Проверка создания поста

        Проверка что созданный пост попал
        на страницы index, group и profile
        """
        cache.clear()
        for reverse_name in self.page_name:
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                objects = response.context['page_obj']
                self.assertIn(self.post_1, objects)

    def test_post_create_not_contains_another_group(self):
        """Проверка что пост не попал в другую группу"""
        response = self.client.get(
            reverse('posts:group_posts', kwargs={'slug': self.group_2.slug})
        )
        objects = response.context['page_obj']
        self.assertNotIn(self.post_1, objects)


class PostCacheTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Mr.X')
        cls.post_cache = Post.objects.create(
            author=cls.user,
            text='Тестовый текст для поста 1!',
        )

    def test_cash_index(self):
        """Проверка кеширования страницы index"""
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        content_1 = response.content
        self.post_cache.delete()
        response = self.client.get(reverse('posts:index'))
        content_2 = response.content
        self.assertEqual(content_1, content_2)


class FollowingTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Mr.X')

    def test_create_follow_not_authorized(self):
        """Проверка попытки создания подписки."""
        follow_count = Follow.objects.count()
        response = self.client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author}),
        )
        rev_login = reverse('users:login')
        rev_follow = reverse(
            'posts:profile_follow', kwargs={'username': self.author}
        )
        self.assertEqual(Follow.objects.count(), follow_count)
        self.assertRedirects(
            response, f'{rev_login}?next={rev_follow}'
        )

    def test_create_follow_index(self):
        """Проверка появления постов в ленте подписки."""
        follower_1 = User.objects.create_user(username='Mr.Y')
        authorized_client_1 = Client()
        authorized_client_1.force_login(follower_1)
        follower_2 = User.objects.create_user(username='Mr.Z')
        authorized_client_2 = Client()
        authorized_client_2.force_login(follower_2)
        post = Post.objects.create(
            author=self.author,
            text='Тестовый текст для поста!',
        )
        authorized_client_1.get(reverse(
            'posts:profile_follow', kwargs={'username': self.author}),
        )
        response = authorized_client_1.get(reverse('posts:follow_index'))
        objects = response.context['page_obj']
        self.assertIn(post, objects)
        response = authorized_client_2.get(reverse('posts:follow_index'))
        objects = response.context['page_obj']
        self.assertNotIn(post, objects)
