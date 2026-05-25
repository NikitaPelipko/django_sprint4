from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Post, Category
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from .forms import CreatePostForm, UserProfileForm

User = get_user_model()


def index(request):
    template = "blog/index.html"
    posts = Post.objects.filter(
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True,
    ).order_by("-pub_date")[:5]
    context = {"post_list": posts}
    return render(request, template, context)


def post_detail(request, id):
    template = "blog/detail.html"
    post = get_object_or_404(
        Post,
        pk=id,
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True,
    )
    context = {"post": post}
    return render(request, template, context)


def category_posts(request, category_slug):
    template = "blog/category.html"
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True,
    )
    posts = Post.objects.filter(
        category=category,
        is_published=True,
        pub_date__lte=timezone.now(),
    ).order_by("-pub_date")
    context = {"category": category, "post_list": posts}
    return render(request, template, context)


def profile_detail(request, username):
    template = "blog/profile.html"
    profile = get_object_or_404(User, username=username)
    context = {"profile": profile}
    return render(request, template, context)


@login_required
def create_post(request):
    if request.method == 'POST':
        form = CreatePostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('blog:profile', username = request.user.username)
    else:
        form = CreatePostForm()
    return render(request, "blog/create.html", {'form': form})


@login_required
def edit_profile(request):
    profile = request.user
    form = UserProfileForm(request.POST, instance=profile)
    if form.is_valid():
        form.save()
        return redirect('profile', username=profile.username)
    context = {
        'form': form,
    }
    return render(request, 'blog/user.html', context)