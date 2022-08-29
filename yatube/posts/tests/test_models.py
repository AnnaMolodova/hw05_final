from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post


CHARACTERS = 15

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__"""
        task_post = PostModelTest.post.__str__()
        sym_post = PostModelTest.post.text[:CHARACTERS]
        task_group = PostModelTest.group.__str__()
        title_group = PostModelTest.group.title
        self.assertEqual(task_post, sym_post, 'ошибка с отображением')
        self.assertEqual(
            task_group, title_group, 'ошибка в названии группы str'
        )
