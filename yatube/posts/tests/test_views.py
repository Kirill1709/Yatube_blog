import datetime as dt
import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(dir=settings.BASE_DIR))
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="name")
        cls.group_2 = Group.objects.create(
            title="testgroup2",
            slug='test-slug2',
            description='Описание2')
        cls.group = Group.objects.create(
            title="testgroup",
            slug='test-slug',
            description='Описание')
        cls.small_png = (b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x02'
                         b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\xf4"\x7f\x8a'
                         b'\x00\x00\x00\x11IDAT\x08\x99c```\xf8\xff\x9f\x81'
                         b'\xe1?\x00\t\xff\x02\xfe\xaa\x98\xdd\xaf\x00\x00'
                         b'\x00\x00IEND\xaeB`\x82')
        cls.uploaded = SimpleUploadedFile(
            name='small.png',
            content=cls.small_png,
            content_type='image/png'
        )
        cls.post_2 = Post.objects.create(
            text='Тестовый текст2',
            author=User.objects.get(username="name"),
            group=cls.group_2
        )
        cls.post_1 = Post.objects.create(
            text='Тестовый текст1',
            author=User.objects.get(username="name"),
            group=cls.group,
            image=cls.uploaded
        )
        cls.response_name = {
            reverse('posts:index'): 'index',
            reverse('posts:group_posts',
                    kwargs={'slug': cls.group.slug}): 'group',
            reverse('posts:profile',
                    kwargs={'username': cls.user.username}): 'profile',
        }
        cls.templates_pages = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_posts',
                    kwargs={'slug': cls.group.slug}): 'group.html',
            reverse('posts:new_post'): 'posts/new_post.html',
        }

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)
        cache.clear()

    def checks_the_fields_of_the_post(self, post, expected_post):
        """Проверка ожидаемых и действительных значений."""
        post_text_0 = expected_post.text
        post_pub_date_0 = (expected_post.pub_date).replace(
            second=0,
            microsecond=0)
        post_author_0 = expected_post.author
        post_group_0 = expected_post.group
        self.assertEqual(post_text_0, post.text),
        self.assertEqual(
            post_pub_date_0,
            dt.datetime.today().replace(
                second=0,
                microsecond=0)),
        self.assertEqual(post_author_0, self.user),
        self.assertEqual(post_group_0, post.group)

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, template in PostPagesTests.templates_pages.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_new_post_shows_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:new_post'))
        response_edit = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'username': 'name', 'post_id': '1'}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                form_field_edit = response_edit.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
                self.assertIsInstance(form_field_edit, expected)

    def test_index_list_page_shows_correct_context(self):
        """Шаблон index и group сформирован с правильным контекстом,
        а также проверка отображения созданного поста на главной
         странице и в группе"""
        for reverse_name, _ in PostPagesTests.response_name.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                post = response.context['page'][0]
                self.checks_the_fields_of_the_post(post, PostPagesTests.post_1)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'username': 'name',
                                               'post_id': '1'})
        )
        post = response.context['post']
        self.checks_the_fields_of_the_post(post, PostPagesTests.post_2)

    def test_post_not_equal_show_correct_context(self):
        """Проверка поста, не принадлежащего данной группе."""
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': 'test-slug2'}))
        post = response.context['page'][0]
        self.checks_the_fields_of_the_post(post, PostPagesTests.post_2)

    def test_post_image_correct_context(self):
        """Проверка наличия ожидаемого изображения в контексте
        главной страницы, страницы группы и профайла."""
        for reverse_name in PostPagesTests.response_name:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                post = response.context['page'][0]
                self.assertEqual(post.image, PostPagesTests.post_1.image)

    def test_post_image_correct_context_in_view_page(self):
        """Проверка наличия ожидаемого изображения в контексте
        отдельного поста."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_view', kwargs={
                    'username': PostPagesTests.user,
                    'post_id': PostPagesTests.post_1.id,
                }
            )
        )
        post = response.context['post']
        self.assertEqual(post.image, PostPagesTests.post_1.image)

    def test_cache_operation(self):
        """Проверка кэша главной страницы."""
        self.authorized_client.get(reverse('posts:index'))
        key = make_template_fragment_key('index_page')
        result = cache.get(key)
        self.assertIsNotNone(result)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="name")
        cls.group_2 = Group.objects.create(
            title="testgroup2",
            slug='test-slug2',
            description='Описание2')
        cls.group = Group.objects.create(
            title="testgroup",
            slug='test-slug',
            description='Описание')
        posts = [Post(
            text=f'Тестовый текст{i}',
            author=cls.user,
            group=cls.group_2) for i in range(1, 12)]
        Post.objects.bulk_create(posts)

    def setUp(self):
        self.guest_client = Client()

    def test_first_page_contains_ten_records(self):
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_page_contains_one_records(self):
        response = self.guest_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 1)
