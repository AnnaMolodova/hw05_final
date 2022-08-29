from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator

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
    template = "posts/profile.html"
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author_id=author.id)
    count = posts.count
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    user = request.user
    following = False
    if (not user.is_anonymous) and Follow.objects.filter(
        user=user, author=author
    ).exists():
        following = True
    context = {
        "count": count,
        "author": author,
        "page_obj": page_obj,
        "following": following,
    }
    return render(request, template, context)



def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    form = CommentForm()
    context = {
        'post': post,
        'comments': comments,
        'form': form
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
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
    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
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
        template,
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
    paginator = Paginator(posts, 10)
    page_nuber = request.GET.get('page')
    page_obj = paginator.get_page(page_nuber)
    context = {
        'page_obj': page_obj
    }
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
        author = get_object_or_404(User, username=username)
        )
    return redirect('posts:profile', username)

@login_required
def profile_unfollow(request, username):
    unfollow = Follow.objects.get(
        user=get_object_or_404(User, username=request.user.username),
        author = get_object_or_404(User, username=username)
    )
    unfollow.delete()
    return redirect('posts:profile', username)
