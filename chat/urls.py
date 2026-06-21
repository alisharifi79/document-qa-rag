from django.urls import path
from .views import (
    admin_ask_page,
    new_admin_chat,
    ask,
    delete_admin_chat,
)
urlpatterns = [
    path("ask/", ask),
    path("admin-ask/", admin_ask_page, name="admin_ask"),
    path("admin-ask/new/", new_admin_chat, name="new_admin_chat"),
    path("admin-ask/<int:chat_id>/", admin_ask_page, name="admin_ask_chat"),
    path(
    "admin-ask/delete/<int:chat_id>/",
    delete_admin_chat,
    name="delete_admin_chat"
),
]