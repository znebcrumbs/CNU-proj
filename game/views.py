from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
import random
import string
import json
from .models import GameRoom, Player, PartCard, FunctionCard, PlayerCard
from .utils import draw_function_card, is_correct_part, handle_correct_play, handle_incorrect_play, deal_initial_cards

def generate_room_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def lobby(request):
    if request.method == "POST":
        nickname = request.POST.get("nickname")
        room_code = request.POST.get("room_code")

        if not nickname:
            return render(request, "lobby.html", {"error": "Nickname required"})

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
    player_id = request.session.get("player_id")
    is_host = False
    if player_id:
        try:
            player = Player.objects.get(id=player_id)
            is_host = player.is_host
        except Player.DoesNotExist:
            pass
    return render(request, "game_room.html", {
        "room_code": room_code,
        "player_id": player_id,
        "is_host": is_host,
    })

def game_board(request, room_code):
    player_id = request.session.get("player_id")
    if not player_id:
        return redirect("lobby")
    
    player = get_object_or_404(Player, id=player_id)
    if player.is_finished:
        return redirect("game_room", room_code=room_code)

    return render(request, "game_board.html", {
        "room_code": room_code,
        "player_id": player_id,
    })

# AJAX ENDPOINTS

def get_leaderboard(request, room_code):
    player_id = request.session.get("player_id")
    if not player_id:
        return JsonResponse({"error": "No session"}, status=403)
    
    room = get_object_or_404(GameRoom, code=room_code)
    players = room.players.all().order_by("-accuracy")
    data = [
        {
            "nickname": p.nickname,
            "accuracy": p.accuracy,
            "role": "Host" if p.is_host else "Member",
            "is_finished": p.is_finished
        } for p in players
    ]
    return JsonResponse({"players": data})

@require_POST
def start_mission(request, room_code):
    player_id = request.session.get("player_id")
    if not player_id:
        return JsonResponse({"error": "No session"}, status=403)

    try:
        with transaction.atomic():
            player = Player.objects.select_for_update().get(id=player_id)
            if player.is_finished:
                return JsonResponse({"error": "Mission already completed"}, status=400)

            existing_cards = PlayerCard.objects.filter(player=player, is_used=False).exists()

            if not existing_cards:
                PlayerCard.objects.filter(player=player).delete()
                player.accuracy = 0
                player.turns_played = 0
                player.save()
                try:
                    deal_initial_cards(player)
                except ValueError as e:
                    return JsonResponse({"error": str(e)}, status=500)
                try:
                    func_card = draw_function_card()
                except ValueError as e:
                    return JsonResponse({"error": str(e)}, status=500)
                request.session["current_func_card_id"] = func_card.id
            else:
                func_card_id = request.session.get("current_func_card_id")
                try:
                    func_card = (
                        FunctionCard.objects.get(id=func_card_id)
                        if func_card_id
                        else draw_function_card()
                    )
                except (FunctionCard.DoesNotExist, ValueError):
                    try:
                        func_card = draw_function_card()
                    except ValueError as e:
                        return JsonResponse({"error": str(e)}, status=500)
                request.session["current_func_card_id"] = func_card.id
    except Player.DoesNotExist:
        from django.http import Http404
        raise Http404

    hand = [
        {"id": c.part_card.id, "name": c.part_card.name}
        for c in PlayerCard.objects.filter(player=player, is_used=False)
    ]

    return JsonResponse({
        "status": "resumed" if existing_cards else "started",
        "hand": hand,
        "objective": func_card.description,
        "objective_id": func_card.id,
        "accuracy": player.accuracy,
        "turns_played": player.turns_played,
    })

@require_POST
def play_card_ajax(request, room_code):
    player_id = request.session.get("player_id")
    if not player_id:
        return JsonResponse({"error": "No session"}, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    part_card_id = data.get("part_card_id")
    current_func_id = data.get("objective_id")

    player = get_object_or_404(Player, id=player_id)
    if player.is_finished:
        return JsonResponse({"error": "Game over"}, status=400)

    part_card = get_object_or_404(PartCard, id=part_card_id)
    func_card = get_object_or_404(FunctionCard, id=current_func_id)

    correct = is_correct_part(func_card, part_card)

    if correct:
        player_card = PlayerCard.objects.filter(player=player, part_card=part_card).first()
        if player_card:
            handle_correct_play(player, player_card)
        result = "correct"
    else:
        handle_incorrect_play(player)
        result = "incorrect"

    player.turns_played += 1
    player.save(update_fields=["accuracy", "turns_played"])

    try:
        next_func = draw_function_card()
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=500)
    request.session["current_func_card_id"] = next_func.id

    game_over = player.turns_played >= 10

    return JsonResponse({
        "result": result,
        "accuracy": player.accuracy,
        "next_objective": next_func.description,
        "next_objective_id": next_func.id,
        "hand": [
            {"id": c.part_card.id, "name": c.part_card.name}
            for c in PlayerCard.objects.filter(player=player, is_used=False)
        ],
        "game_over": game_over,
        "turns_played": player.turns_played,
    })

@require_POST
def finish_game(request, room_code):
    player_id = request.session.get("player_id")
    if not player_id:
        return JsonResponse({"error": "No session"}, status=403)

    player = get_object_or_404(Player, id=player_id)
    player.is_finished = True
    player.save()
    return JsonResponse({"status": "finished"})
