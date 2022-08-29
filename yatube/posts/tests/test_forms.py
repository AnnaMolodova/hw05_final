import shutil
import tempfile
from urllib import response

from posts.models import Group, Post, User, Comment
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тест группа',
            slug='test-slug',
            description='Тест описание',
        )

        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            author=cls.author,
            text='Тест пост',
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_post_create(self):
        """Валидная форма создания поста."""
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'текст',
            'author': self.author,
            'group': self.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(reverse(
            'posts:post_create'
        ), data=form_data, follow=True)
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.author.username}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='текст',
                author=self.author
            ).exists()
        )

    def test_post_edit(self):
        """При редактировании поста запись меняется в БД."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Редактируемый текст',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse(('posts:post_edit'), kwargs={
                'post_id': self.post.id}),
            data=form_data, follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            args=(1,)
        ))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text='Редактируемый текст',
                group=self.group.id
            ).exists()
        )
    
    def test_img_index(self):
        """В index изображение передается в словаре context."""
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        post = response.context['page_obj'][0].image.name
        self.assertEqual(post, 'posts/small.gif')
    
    def test_img_profile(self):
        """В profile изображение передается в словаре context."""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': 'auth'}
            )
        )
        post = response.context['page_obj'][0].image.name
        self.assertEqual(post, 'posts/small.gif')
    
    def test_img_group(self):
        """В profile изображение передается в словаре context."""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            )
        )
        group = response.context['page_obj'][0].image.name
        self.assertEqual(group, 'posts/small.gif')
    
    def test_img_post_detail(self):
        """В post_detail изображение передается в словаре context."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': '1'}
            )
        )
        post_detail = response.context['post'].image.name
        self.assertEqual(post_detail, 'posts/small.gif')


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.post = Post.objects.create(
            author=cls.user,
            text= 'Вот текст'
        )
    
    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
    
    def test_comment_auth_user(self):
        """Комментарии могут писать только авторизованные юзеры."""
        form_data = {
            'text': 'Вот такой текст'
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        self.assertTrue(
            Comment.objects.filter(text='Вот такой текст').exists()
        )
    
    def test_comment_show_post_detail(self):
        """Комментарий появляется на странице поста."""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Коммент'
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
