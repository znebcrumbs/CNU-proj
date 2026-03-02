from django.shortcuts import render

# Create your views here.
import random
import string
from django.shortcuts import render, redirect
from .models import GameRoom, Player

def generate_room_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def lobby(request):
    if request.method == "POST":
        nickname = request.POST.get("nickname")
        room_code = request.POST.get("room_code")

        if not nickname:
            return render(request, "lobby.html", {"error": "Nickname required"})

        # Create new room
        if not room_code:
            room_code = generate_room_code()
            room = GameRoom.objects.create(code=room_code)
            is_host = True
        else:
            try:
                room = GameRoom.objects.get(code=room_code)
            except GameRoom.DoesNotExist:
                return render(request, "lobby.html", {"error": "Room not found"})
            is_host = False

        player = Player.objects.create(
            nickname=nickname,
            room=room,
            is_host=is_host
        )

        request.session["player_id"] = player.id
        request.session["room_code"] = room.code

        return redirect("game_room", room_code=room.code)

    return render(request, "lobby.html")

def game_room(request, room_code):
    return render(request, "game_room.html", {
        "room_code": room_code,
        "player_id": request.session.get("player_id")
    })
def game_board(request, room_code):
    # safety check (optional but good)
    if "player_id" not in request.session:
        return redirect("lobby")

    return render(request, "game_board.html", {
        "room_code": room_code,
        "player_id": request.session.get("player_id"),
    })