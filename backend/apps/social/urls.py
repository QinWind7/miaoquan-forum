from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    FollowToggleView,
    FollowerListView,
    FriendListView,
    FriendRequestViewSet,
)

router = DefaultRouter()
router.register("social/friend-requests", FriendRequestViewSet, basename="friend-request")

urlpatterns = [
    path(
        "social/users/<int:pk>/follow/",
        FollowToggleView.as_view(),
        name="social-follow",
    ),
    path(
        "social/users/<int:pk>/followers/",
        FollowerListView.as_view(),
        name="social-followers",
    ),
    path("social/friends/", FriendListView.as_view(), name="social-friends"),
] + router.urls
