from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Mr.X')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст!!!!!!!!!!!',
        )

    def test_models_have_correct_object_names_post_group(self):
        """Проверяем, что у модели Post И Group корректно работает __str__."""
        object_name = (
            (self.post.text[:15], self.post),
            (self.group.title, self.group),
        )
        for objects, name in object_name:
            with self.subTest(objects=objects):
                self.assertEqual(objects, str(name))
