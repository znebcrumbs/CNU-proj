from django.urls import path
from . import views

urlpatterns = [
    path("", views.lobby, name="lobby"),
    path("room/<str:room_code>/", views.game_room, name="game_room"),
    path("game/<str:room_code>/", views.game_board, name="game_board"),
    path("game/<str:room_code>/", views.game_board, name="game_board"),
]