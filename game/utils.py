import random
from .models import PartCard, PlayerCard, Player, FunctionCard

def draw_function_card():
    cards = list(FunctionCard.objects.all())
    if not cards:
        raise ValueError("No FunctionCards in database. Please seed data.")
    return random.choice(cards)

def is_correct_part(function_card, part_card):
    return function_card.correct_part == part_card

def handle_correct_play(player, player_card, accuracy_gain=10):
    player_card.delete()
    player.accuracy = min(player.accuracy + accuracy_gain, 100)

def handle_incorrect_play(player, penalty_cards=2):
    available_parts = list(PartCard.objects.all())
    if not available_parts:
        return

    random.shuffle(available_parts)
    count = min(penalty_cards, len(available_parts))
    for i in range(count):
        PlayerCard.objects.create(
            player=player,
            part_card=available_parts[i],
            room=player.room
        )

def deal_initial_cards(player, count=5):
    all_parts = list(PartCard.objects.all())
    if len(all_parts) < count:
        raise ValueError(f"Not enough PartCards in database (need {count}).")

    random.shuffle(all_parts)
    for i in range(count):
        PlayerCard.objects.create(
            player=player,
            part_card=all_parts[i],
            room=player.room
        )
