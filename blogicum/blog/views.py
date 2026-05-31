from django.shortcuts import get_object_or_404, redirect
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse_lazy
from .models import Post, Category, Comment
from .forms import CreatePostForm, UserProfileForm, CommentForm
from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied
from django.http import Http404
from .mixins import CommentCountMixin, PaginationMixin

User = get_user_model()


class IndexView(PaginationMixin, CommentCountMixin, ListView):
    """Главная страница со списком постов"""

    model = Post
    template_name = "blog/index.html"
    context_object_name = "post_list"

    def get_queryset(self):
        return self.get_posts_with_comments(user=self.request.user)


class PostDetailView(DetailView):
    """Детальная страница поста"""

    model = Post
    template_name = "blog/detail.html"
    context_object_name = "post"
    pk_url_kwarg = "post_id"

    def get_queryset(self):
        queryset = Post.objects.select_related(
            "author", "category", "location"
        ).prefetch_related("comments__author")
        return queryset

    def get_object(self, queryset=None):
        post = super().get_object(queryset)
        category_is_published = post.category is not None and post.category.is_published

        if (
            post.is_published
            and post.pub_date <= timezone.now()
            and category_is_published
        ):
            return post

        if self.request.user == post.author:
            return post

        raise Http404("Пост не найден или не опубликован")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comments"] = self.object.comments.all()
        context["form"] = CommentForm()
        return context


class CreatePostView(LoginRequiredMixin, CreateView):
    """Создание нового поста"""

    model = Post
    form_class = CreatePostForm
    template_name = "blog/create.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "blog:profile", kwargs={"username": self.request.user.username}
        )


class EditPostView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование поста"""

    model = Post
    form_class = CreatePostForm
    template_name = "blog/create.html"
    pk_url_kwarg = "post_id"

    def dispatch(self, request, *args, **kwargs):
        """Проверка авторизации и прав доступа"""
        if not request.user.is_authenticated:
            post = get_object_or_404(Post, pk=self.kwargs["pk"])
            return redirect("blog:post_detail", id=post.id)

        post = self.get_object()
        if post.author != request.user:
            return redirect("blog:post_detail", id=post.id)

        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        post = self.get_object()
        return post.author == self.request.user

    def get_success_url(self):
        return reverse_lazy(
            "blog:profile", kwargs={"username": self.request.user.username}
        )

    def form_valid(self, form):
        return super().form_valid(form)


class DeletePostView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Удаление поста"""

    model = Post
    template_name = "blog/create.html"
    pk_url_kwarg = "post_id"
    context_object_name = "post"

    def test_func(self):
        post = self.get_object()
        return post.author == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = CreatePostForm(instance=self.get_object())
        return context

    def get_success_url(self):
        return reverse_lazy(
            "blog:profile", kwargs={"username": self.request.user.username}
        )


class CategoryPostsView(PaginationMixin, CommentCountMixin, ListView):
    """Посты по категориям"""

    model = Post
    template_name = "blog/category.html"
    context_object_name = "post_list"

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs["category_slug"],
            is_published=True,
        )
        return self.get_posts_with_comments(
            category=self.category, user=self.request.user
        )

        

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.category

        return context


class ProfileDetailView(PaginationMixin, CommentCountMixin, DetailView):
    """Страница профиля пользователя"""

    model = User
    template_name = "blog/profile.html"
    context_object_name = "profile"
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_object(self, queryset=None):
        return get_object_or_404(
            User.objects.prefetch_related(
                "posts__comments", "posts__category", "posts__location"
            ),
            username=self.kwargs["username"],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user_posts = self.get_posts_with_comments(user=self.request.user)
        user_posts = user_posts.filter(author=self.object)

        if self.request.user != self.object:
            user_posts = user_posts.filter(
                is_published=True, pub_date__lte=timezone.now()
            )

        context['page_obj'] = self.paginate_queryset(user_posts)

        return context


class EditProfileView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование профиля"""

    model = User
    form_class = UserProfileForm
    template_name = "blog/user.html"

    def get_object(self, queryset=None):
        return self.request.user

    def test_func(self):
        return self.get_object() == self.request.user

    def get_success_url(self):
        return reverse_lazy(
            "blog:profile", kwargs={"username": self.request.user.username}
        )

    def form_valid(self, form):
        return super().form_valid(form)


class CommentCreateView(LoginRequiredMixin, CreateView):
    """Создание комментария"""

    model = Comment
    form_class = CommentForm
    http_method_names = ["post"]

    def form_valid(self, form):
        post = get_object_or_404(Post, id=self.kwargs["post_id"])
        form.instance.author = self.request.user
        form.instance.post = post
        response = super().form_valid(form)

        if post.author.email:
            send_mail(
                subject="Новый комментарий к вашему посту",
                message=(
                    f"Пользователь {self.request.user.username} оставил комментарий "
                    f"под вашим постом «{post.title}»:\n\n"
                    f"{form.instance.text}"
                ),
                from_email=None,
                recipient_list=[post.author.email],
                fail_silently=True,
            )

        return response

    def get_success_url(self):
        return reverse_lazy("blog:post_detail", kwargs={"id": self.kwargs["post_id"]})


class CommentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование комментария"""

    model = Comment
    form_class = CommentForm
    template_name = "blog/comment.html"
    pk_url_kwarg = "comment_id"

    def get_object(self, queryset=None):
        """Получаем комментарий с проверкой существования"""
        comment_id = self.kwargs.get("comment_id")
        post_id = self.kwargs.get("post_id")

        comment = get_object_or_404(
            Comment.objects.select_related("author", "post"),
            id=comment_id,
            post_id=post_id,
        )

        if comment.author != self.request.user:
            raise PermissionDenied("Вы не можете редактировать чужой комментарий")

        return comment

    def test_func(self):
        try:
            comment = self.get_object()
            return comment.author == self.request.user
        except (Comment.DoesNotExist, AttributeError):
            return False

    def get_queryset(self):
        return Comment.objects.select_related("author", "post")

    def get_success_url(self):
        return reverse_lazy("blog:post_detail", kwargs={"id": self.object.post.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["post_id"] = self.kwargs["post_id"]
        context["comment_id"] = self.kwargs["comment_id"]
        return context


class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Удаление комментария"""

    model = Comment
    template_name = "blog/comment.html"
    pk_url_kwarg = "comment_id"
    context_object_name = "comment"

    def test_func(self):
        comment = self.get_object()
        return comment.author == self.request.user or self.request.user.is_staff

    def get_queryset(self):
        return Comment.objects.select_related("post")

    def get_success_url(self):
        return reverse_lazy("blog:post_detail", kwargs={"id": self.object.post.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["post_id"] = self.kwargs["post_id"]
        context["comment_id"] = self.kwargs["comment_id"]
        return context
