from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username="name",
            email="email@mail.com", password="Pass12345")
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
        )

    def test_object_post_name_is_title_field(self):
        post = PostModelTest.post
        expected_object_name = post.text
        self.assertEqual(str(post), expected_object_name)


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый текст'
        )

    def test_object_group_name_is_title_field(self):
        group = GroupModelTest.group
        expected_object_name = group.title
        self.assertEquals(str(group), expected_object_name)
