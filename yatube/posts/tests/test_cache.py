from django.core.cache import cache


from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, Group

User = get_user_model()


class CacheViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='test-group',
            slug='test-slug',
            description='Описание'
        )
        cls.post = Post.objects.create(
            text='test_post',
            group=cls.group,
            author=cls.author
        )

    def test_cache_index(self):
        """Работа кэша в index."""
        response = CacheViewsTest.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='Вот такой текст',
            author=CacheViewsTest.author,
        )
        response_1 = CacheViewsTest.authorized_client.get(reverse('posts:index'))
        posts_1 = response_1.content
        self.assertEqual(posts_1, posts)
        cache.clear()
        response_2 = CacheViewsTest.authorized_client.get(reverse('posts:index'))
        posts_2 = response_2.content
        self.assertNotEqual(posts_1, posts_2)
