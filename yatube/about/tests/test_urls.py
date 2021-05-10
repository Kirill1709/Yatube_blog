from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.public_urls = (
            '/about/author/',
            '/about/tech/',
        )

    def setUp(self):
        self.guest_client = Client()

    def test_anonymous_user_has_access_to_the_addresses(self):
        """Страница /about/author/ и /about/tech/
        доступна любому пользователю."""
        for url in self.public_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 200)
