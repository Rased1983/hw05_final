from django.test import TestCase

from http import HTTPStatus


class StaticURLTests(TestCase):

    def test_about_author_and_tech(self):
        url = (
            '/about/author/',
            '/about/tech/',
        )
        for address in url:
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
