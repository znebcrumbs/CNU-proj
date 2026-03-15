import random
from django.db import transaction
from .models import PartCard, PlayerCard, Player, FunctionCard


def draw_function_card():
    cards = list(FunctionCard.objects.all())
    if not cards:
        raise ValueError("No FunctionCards in database. Please seed data.")
    return random.choice(cards)

def is_correct_part(function_card, part_card):
    return function_card.correct_part == part_card

def handle_correct_play(player, player_card, accuracy_gain=5):
    player_card.delete()
    # Increment streak and calculate accuracy based on streak
    player.consecutive_correct_plays += 1
    accuracy_gain = 5 * player.consecutive_correct_plays  # Scale: 1st=5, 2nd=10, 3rd=15, etc.
    player.accuracy = min(player.accuracy + accuracy_gain, 100)
    player.cards_to_deal -= 1
    player.save()

def handle_incorrect_play(player, func_card):
    player.accuracy = max(player.accuracy - 10, 0)
    player.consecutive_correct_plays = 0  # Reset streak on incorrect play
    player.cards_to_deal = min(player.cards_to_deal + 1, 7)  # Cap at 7
    PlayerCard.objects.filter(player=player).delete()
    deal_initial_cards(player, func_card, count=player.cards_to_deal)
    player.save()

def deal_initial_cards(player, func_card, count=5, max_attempts=20):
    """
    Deal a random hand of `count` cards.
    Discard and retry until the hand contains the correct part for func_card.
    Falls back to forcing the correct card in after max_attempts.
    """
    all_parts = list(PartCard.objects.all())
    if len(all_parts) < count:
        raise ValueError(f"Not enough PartCards in database (need at least {count}).")

    correct_part = func_card.correct_part

    hand = None
    for _ in range(max_attempts):
        candidate = random.sample(all_parts, count)
        if any(p.id == correct_part.id for p in candidate):
            hand = candidate
            break

    if hand is None:
        others = [p for p in all_parts if p.id != correct_part.id]
        hand = [correct_part] + random.sample(others, min(count - 1, len(others)))
        random.shuffle(hand)

    for part in hand:
        PlayerCard.objects.create(
            player=player,
            part_card=part,
            room=player.room
        )

def ensure_correct_part_in_hand(player, func_card):
    """Add the correct part card to hand if it is not already there."""
    correct_part = func_card.correct_part
    with transaction.atomic():
        already_present = PlayerCard.objects.select_for_update().filter(
            player=player,
            part_card=correct_part,
            is_used=False
        ).exists()
        if not already_present:
            PlayerCard.objects.create(
                player=player,
                part_card=correct_part,
                room=player.room
            )

def deal_cards_for_correct_play(player, func_card):
    """Deal cards based on player.cards_to_deal after a correct play."""
    PlayerCard.objects.filter(player=player).delete()
    deal_initial_cards(player, func_card, count=player.cards_to_deal)
