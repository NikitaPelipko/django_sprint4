from django.db.models import Count, Q
from django.utils import timezone
from .models import Post
from django.core.paginator import Paginator


class CommentCountMixin:
    """
    Миксин для добавления количества комментариев к постам.
    """

    def get_posts_with_comments(self, base_queryset=None, user=None, category=None):
        if base_queryset is None:
            queryset = Post.objects.all()
        else:
            queryset = base_queryset

        queryset = queryset.select_related(
            "author", "category", "location"
        ).prefetch_related("comments")

        queryset = queryset.annotate(comment_count=Count("comments"))

        queryset = queryset.order_by("-pub_date")

        if category:
            queryset = queryset.filter(category=category)

        if user and user.is_authenticated:
            queryset = queryset.filter(
                Q(author=user)
                | Q(
                    is_published=True,
                    pub_date__lte=timezone.now(),
                    category__is_published=True,
                )
            )
        else:
            queryset = queryset.filter(
                is_published=True,
                pub_date__lte=timezone.now(),
                category__is_published=True,
            )

        return queryset

class PaginationMixin:
    """
    Миксин для пагинации.
    """

    page_size = 10

    def paginate_queryset(self, queryset):
        page_number = self.request.GET.get('page', 1)
        paginator = Paginator(queryset, self.page_size)
        return paginator.get_page(page_number)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'object_list'):
            page_obj = self.paginate_queryset(self.object_list)
            context['page_obj'] = page_obj
            context['is_paginated'] = True
            context['paginator'] = page_obj.paginator
            context['object_list'] = page_obj  
        
        return context

