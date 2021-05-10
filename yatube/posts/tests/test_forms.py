import datetime as dt
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import PostForm

from ..models import Comment, Follow, Group, Post

User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(dir=settings.BASE_DIR))
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Post.objects.create(
            text='Тестовый текст',
            author=User.objects.create_user(username="name",
                                            email="email@mail.com",
                                            password="Pass12345"),
            group=Group.objects.create(title="testgroup", slug='test-slug',
                                       description='Описание')
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.get(username='name')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.get(title="testgroup")

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        small_png = (b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x02'
                     b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\xf4"\x7f\x8a'
                     b'\x00\x00\x00\x11IDAT\x08\x99c```\xf8\xff\x9f\x81'
                     b'\xe1?\x00\t\xff\x02\xfe\xaa\x98\xdd\xaf\x00\x00'
                     b'\x00\x00IEND\xaeB`\x82')
        uploaded = SimpleUploadedFile(
            name='small.png',
            content=small_png,
            content_type='image/png'
        )
        form_data = {
            'text': 'Тестовый текст2',
            'pub_date': dt.datetime.today(),
            'author': self.user,
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:new_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст2',
                group=self.group.id,
                image='posts/small.png'
            ).exists()
        )

    def test_change_post(self):
        """Валидная форма редактирует запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст3',
            'pub_date': dt.datetime.today(),
            'author': self.user,
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'username': 'name',
                                               'post_id': '1'}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, '/name/1/')
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст3',
                group=self.group.id
            ).exists()
        )


class SubscriptionsFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create_user(username="name1")
        cls.user_2 = User.objects.create_user(username="name2")
        cls.user_3 = User.objects.create_user(username="name3")
        cls.group = Group.objects.create(
            title="testgroup",
            slug='test-slug',
            description='Описание')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user_1,
            group=cls.group
        )
        cls.follow = Follow.objects.create(
            user=cls.user_1,
            author=cls.user_2)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client_1 = Client()
        self.authorized_client_1.force_login(SubscriptionsFormTest.user_1)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(SubscriptionsFormTest.user_2)
        self.authorized_client_3 = Client()
        self.authorized_client_3.force_login(SubscriptionsFormTest.user_3)

    def test_autorized_client_subscribe(self):
        """Проверка возможности подписки одного пользователя на другого."""
        follow_count = Follow.objects.filter(
            user=self.user_3, author=self.user_2).count()
        self.authorized_client_3.post(
            reverse('posts:profile_follow', kwargs={
                'username': self.user_2.username}),
            follow=True
        )
        self.assertEqual(Follow.objects.filter(
            user=self.user_3, author=self.user_2).count(), follow_count + 1)

    def test_autorized_client_unsubscribe(self):
        """Проверка возможности отписки."""
        follow_count = Follow.objects.filter(
            user=self.user_1, author=self.user_2).count()
        self.authorized_client_1.post(
            reverse('posts:profile_unfollow', kwargs={
                'username': self.user_2.username}),
            follow=True
        )
        self.assertEqual(Follow.objects.filter(
            user=self.user_1, author=self.user_2).count(), follow_count - 1)

    def test_displaying_a_post_for_subscribed_users(self):
        """Пост отображается у автора поста и подсписанного на
        него пользователя, в свою очередь у не подписанного нет."""
        posts_count_1 = Post.objects.filter(
            author=SubscriptionsFormTest.user_2).count()
        posts_count_2 = Post.objects.filter(
            author__following__user=SubscriptionsFormTest.user_1).count()
        posts_count_3 = Post.objects.filter(
            author__following__user=SubscriptionsFormTest.user_3).count()
        form_data = {
            'text': 'Тестовый текст2',
            'pub_date': dt.datetime.today(),
            'author': self.user_2,
            'group': self.group.id,
        }
        self.authorized_client_2.post(
            reverse('posts:new_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.filter(
            author=SubscriptionsFormTest.user_2).count(), posts_count_1 + 1)
        self.assertEqual(Post.objects.filter(
            author__following__user=SubscriptionsFormTest.user_1).count(),
            posts_count_2 + 1)
        self.assertEqual(Post.objects.filter(
            author__following__user=SubscriptionsFormTest.user_3).count(),
            posts_count_3)

    def test_autorized_client_can_post_comment(self):
        """Авторизованный пользователь может оставить комментарий
        под постом."""
        comment_count = Comment.objects.all().count()
        form_data = {
            'text': 'Тестовый текст2',
        }
        self.authorized_client_3.post(
            reverse('posts:add_comment', kwargs={
                'username': self.user_1.username, 'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.all().count(), comment_count + 1)

    def test_guest_client_cant_post_comment(self):
        """Неавторизованный пользователь не может оставить комментарий
        под постом."""
        comment_count = Comment.objects.all().count()
        form_data = {
            'text': 'Тестовый текст2',
        }
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={
                'username': self.user_1.username, 'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.all().count(), comment_count)
