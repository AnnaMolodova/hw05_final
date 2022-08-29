from http import HTTPStatus

from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="author")

        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовая пост",
            group=cls.group,
        )

        cls.templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            (reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug}
            )): 'posts/group_list.html',
            (
                reverse('posts:post_create')
            ): 'posts/create_post.html',
            (reverse(
                'posts:post_detail', kwargs={'post_id': cls.post.pk}
            )): 'posts/post_detail.html',
            (reverse(
                'posts:post_edit',
                kwargs={'post_id': cls.post.pk}
            )): 'posts/create_post.html',
            (reverse(
                'posts:profile',
                kwargs={'username': cls.user.username}
            )): 'posts/profile.html',
        }

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        """URL адрес использует нужный шаблон."""
        for address, template in self.templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_guest(self):
        """Страницы, доступные для гостя."""
        page_guest = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.id}/',
        ]
        for address in page_guest:
            response = self.guest_client.get(address)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_authorized(self):
        """Страница для авторизованного пользователя."""
        responses = {
            self.authorized_client.get('/create/'),
        }
        for response in responses:
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page(self):
        """Вернет 404, если страницы не существует."""
        response_guest = self.guest_client.get('/unexisting_page/')
        response_auth = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response_guest.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(response_auth.status_code, HTTPStatus.NOT_FOUND)

    def test_post_edit(self):
        """Шаблон и страница автора доступна только ему
        для редактирования."""
        address = f'/posts/{self.post.id}/edit/'
        template = 'posts/create_post.html'
        response = self.authorized_client.get(address)
        self.assertTemplateUsed(response, template)
        self.assertEqual(response.status_code, HTTPStatus.OK)
