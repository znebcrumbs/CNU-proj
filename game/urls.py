from django.urls import path
from . import views

urlpatterns = [
    path("", views.lobby, name="lobby"),
    path("room/<str:room_code>/", views.game_room, name="game_room"),
    path("game/<str:room_code>/", views.game_board, name="game_board"),
    path("api/room/<str:room_code>/leaderboard/", views.get_leaderboard, name="get_leaderboard"),
    path("api/room/<str:room_code>/start/", views.start_mission, name="start_mission"),
    path("api/room/<str:room_code>/play/", views.play_card_ajax, name="play_card_ajax"),
    path("api/room/<str:room_code>/finish/", views.finish_game, name="finish_game"),
]