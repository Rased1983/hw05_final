from django.conf import settings
from django.test import TestCase


class CastomTeamplateTests(TestCase):

    def test_404_uses_correct_template(self):
        """Страница /unexisting_page/ использует кастомный шаблон."""
        settings.DEBUG = False
        response = self.client.get('/unexisting_page/')
        self.assertTemplateUsed(response, 'core/404.html')
