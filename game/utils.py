import random
from .models import PartCard, PlayerCard, Player, FunctionCard

def deal_part_cards(room, cards_per_player=5):
    players = Player.objects.filter(room=room)
    all_parts = list(PartCard.objects.all())

    random.shuffle(all_parts)

    card_index = 0
    for player in players:
        for _ in range(cards_per_player):
            PlayerCard.objects.create(
                player=player,
                part_card=all_parts[card_index]
            )
            card_index += 1
def draw_function_card():
    cards = list(FunctionCard.objects.all())
    return random.choice(cards)
def is_correct_part(function_card, part_card):
    return function_card.correct_part == part_card
def handle_correct_play(player, player_card, accuracy_gain=10):
    # Remove card from hand
    player_card.delete()

    # Increase accuracy (cap at 100)
    player.accuracy = min(player.accuracy + accuracy_gain, 100)
    player.save()
def handle_incorrect_play(player, penalty_cards=2):
    available_parts = list(PartCard.objects.all())
    random.shuffle(available_parts)

    for i in range(penalty_cards):
        PlayerCard.objects.create(
            player=player,
            part_card=available_parts[i]
        )
def draw_one_part_card(player):
    part = random.choice(PartCard.objects.all())
    PlayerCard.objects.create(
        player=player,
        part_card=part
    )
def rotate_turn(room):
    players = list(Player.objects.filter(room=room).order_by("id"))
    current = next((p for p in players if p.is_turn), None)

    if current:
        current.is_turn = False
        current.save()
        index = players.index(current)
        next_player = players[(index + 1) % len(players)]
    else:
        next_player = players[0]

    next_player.is_turn = True
    next_player.save()
def check_win_condition(player):
    no_cards_left = not PlayerCard.objects.filter(player=player).exists()
    reached_accuracy = player.accuracy >= 80

    return no_cards_left or reached_accuracy


import random
def start_game(room):
    deal_part_cards(room)

    players = room.player_set.all().order_by("id")
    if players.exists():
        players.update(is_turn=False)
        players.first().is_turn = True
        players.first().save()

def deal_part_cards(room):
    players = Player.objects.filter(room=room)
    deck = list(PartCard.objects.all())
    random.shuffle(deck)
    required = players.count() * 5
    available = PartCard.objects.count()

    if available < required:
        raise ValueError("Not enough PartCards to start game")


    for player in players:
        for _ in range(5):
            if not deck:
                return  # or break safely

            card = deck.pop()
            PlayerCard.objects.create(
                player=player,
                part_card=card
            )
