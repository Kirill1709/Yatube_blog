from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create_user(username="name")
        cls.user_2 = User.objects.create_user(username="name2")
        cls.group_1 = Group.objects.create(
            title="testgroup",
            slug='test-slug',
            description='Описание')
        cls.group_2 = Group.objects.create(
            title="testgroup2",
            slug='test-slug2',
            description='Описание2')
        cls.post_1 = Post.objects.create(
            text='Тестовый текст',
            author=cls.user_1,
            group=cls.group_1
        )
        cls.post_2 = Post.objects.create(
            text='Тестовый текст2',
            author=cls.user_2,
            group=cls.group_2
        )
        cls.templates_url_authorized_client = {
            '/new/': 'posts/new_post.html',
            f'/{cls.user_1.username}/{cls.post_1.id}/edit/':
            'posts/new_post.html',
        }
        cls.templates_url_guest_client = {
            '/': 'posts/index.html',
            f'/group/{cls.group_1.slug}/': 'group.html',
            f'/{cls.user_1.username}/': 'posts/profile.html',
            f'/{cls.user_1.username}/{cls.post_1.id}/': 'posts/post.html',
        }
        cls.url_subscriptions = {
            f'/{cls.user_2.username}/follow/': f'/{cls.user_2.username}/',
            f'/{cls.user_2.username}/unfollow/': f'/{cls.user_2.username}/',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user_1)

    def test_url_guest_user_exists_at_desired_location(self):
        """Страницы в словаре доступны любому пользователю."""
        for url in self.templates_url_guest_client:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_task_list_url_exists_at_desired_location(self):
        """Страницы в словаре доступны авторизованному пользователю."""
        for url in self.templates_url_authorized_client:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_anonimus_post_edit_url_exists_at_desired_location(self):
        """Страницы не доступны анонимному пользователю(редирект)."""
        for url in self.templates_url_authorized_client:
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, (f'/auth/login/?next={url}'))

    def test_anonimus_redirect_post_edit_url_exists_at_desired_location(self):
        """Страница /<username>/<post_id>/edit/ не доступна
        не автору поста."""
        response = self.authorized_client.get('/name2/2/edit/')
        self.assertRedirects(
            response, ('/name2/2/'))

    def test_urls_authorized_client_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон
        авторизованного пользователя."""
        for adress, template in self.templates_url_authorized_client.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_urls_guest_client_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон
        анонимного пользователя."""
        for adress, template in self.templates_url_guest_client.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_404_status_for_a_non_existent_page(self):
        """Проверка кода запроса для несуществующей страницы"""
        response = self.guest_client.get('/404/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_subscriptions_and_unsubscriptions_to_the_author(self):
        """Проверка осуществления подписки и отписки
        авторизованного пользователя"""
        for url, redirect_url in self.url_subscriptions.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url, follow=True)
                self.assertRedirects(response, redirect_url)
