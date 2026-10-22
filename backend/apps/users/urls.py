from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .my_center import MyLikesView, MyPostsView
from .profile import UserLikesView, UserPostsView, UserProfileView
from .views import AvatarUploadView, LoginView, LogoutView, MeView, RegisterView

urlpatterns = [
    # 账号与鉴权
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("auth/avatar/", AvatarUploadView.as_view(), name="auth-avatar"),
    # 个人中心
    path("users/my/posts/", MyPostsView.as_view(), name="my-posts"),
    path("users/my/likes/", MyLikesView.as_view(), name="my-likes"),
    # 他人主页（放在 my/ 之后，避免 "my" 被当成 pk）
    path("users/<int:pk>/", UserProfileView.as_view(), name="user-profile"),
    path("users/<int:pk>/posts/", UserPostsView.as_view(), name="user-posts"),
    path("users/<int:pk>/likes/", UserLikesView.as_view(), name="user-likes"),
]
