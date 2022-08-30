from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .models import Group, Post, User, Follow
from .forms import CommentForm, PostForm
from .utils import Create_Page


CACHE_TIME = 20


@cache_page(CACHE_TIME, key_prefix='index_page')
def index(request):
    context = Create_Page(Post.objects.all(), request)
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group)
    context = {
        'group': group,
        'posts': posts
    }
    context.update(Create_Page(Post.objects.all(), request))
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author_id=author.id)
    user = request.user
    following = False
    if (not user.is_anonymous) and Follow.objects.filter(
        user=user, author=author
    ).exists():
        following = True
    context = {
        "author": author,
        "following": following,
    }
    context.update(Create_Page(posts, request))
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    form = CommentForm()
    context = {
        'post': post,
        'comments': comments,
        'form': form
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        temp_form = form.save(commit=False)
        temp_form.author = request.user
        temp_form.save()
        return redirect(
            'posts:profile', temp_form.author
        )
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect(
            'posts:post_detail', post_id
        )
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect(
            'posts:post_detail', post_id
        )
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(
        request,
        'posts/create_post.html',
        context
    )


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, pk=post_id)
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    context = Create_Page(posts, request)
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author and not Follow.objects.filter(
        user=request.user,
        author=author
    ).exists():
        Follow.objects.create(
            user=get_object_or_404(User, username=request.user.username),
            author=get_object_or_404(User, username=username)
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    unfollow = Follow.objects.get(
        user=get_object_or_404(User, username=request.user.username),
        author=get_object_or_404(User, username=username)
    )
    unfollow.delete()
    return redirect('posts:profile', username)
