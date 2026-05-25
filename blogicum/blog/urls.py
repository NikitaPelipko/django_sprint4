from django.urls import path
from . import views

app_name = "blog"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("posts/<int:id>/", views.PostDetailView.as_view(), name="post_detail"),
    path("posts/<int:pk>/edit/", views.EditPostView.as_view(), name="edit_post"),
    path("posts/<int:pk>/delete/", views.DeletePostView.as_view(), name="delete_post"),
    path("posts/create/", views.CreatePostView.as_view(), name="create_post"),
    path("posts/<int:post_id>/comment/", views.CommentCreateView.as_view(), name="add_comment"),
    path("posts/<int:post_id>/edit_comment/<int:comment_id>/", views.CommentUpdateView.as_view(), name="edit_comment"),
    path("posts/<int:post_id>/delete_comment/<int:comment_id>/", views.CommentDeleteView.as_view(), name="delete_comment"),
    path("category/<slug:category_slug>/", views.CategoryPostsView.as_view(), name="category_posts"),
    path("profile/edit/", views.EditProfileView.as_view(), name="edit_profile"),
    path("profile/<str:username>/", views.ProfileDetailView.as_view(), name="profile"),
]