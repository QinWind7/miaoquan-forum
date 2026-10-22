from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ConversationListView, MessageViewSet

router = DefaultRouter()
router.register("chat/messages", MessageViewSet, basename="chat-message")

urlpatterns = [
    path(
        "chat/conversations/",
        ConversationListView.as_view(),
        name="chat-conversations",
    ),
] + router.urls
