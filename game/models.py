from django.db import models
import uuid
from dataclasses import dataclass

class GameRoom(models.Model):
    code = models.CharField(max_length=8, unique=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Room {self.code}"
class Player(models.Model):
    nickname = models.CharField(max_length=20)
    room = models.ForeignKey(GameRoom, on_delete=models.CASCADE, related_name="players")
    accuracy = models.PositiveIntegerField(default=0)
    is_turn = models.BooleanField(default=False)
    is_host = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)  # Updated every time player sends data

    def __str__(self):
        return self.nickname
class Card(models.Model):
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to="cards/", blank=True, null=True)

    class Meta:
        abstract = True
class PartCard(Card):
    OPTICAL = "OPT"
    MECHANICAL = "MECH"
    ILLUMINATING = "ILL"

    CATEGORY_CHOICES = [
        (OPTICAL, "Optical"),
        (MECHANICAL, "Mechanical"),
        (ILLUMINATING, "Illuminating"),
    ]

    category = models.CharField(
        max_length=5,
        choices=CATEGORY_CHOICES
    )

    def __str__(self):
        return self.name
class FunctionCard(Card):
    description = models.TextField()
    correct_part = models.ForeignKey(
        PartCard,
        on_delete=models.CASCADE,
        related_name="functions"
    )
    difficulty = models.PositiveSmallIntegerField(default=1)

    def __str__(self):
        return self.description[:30]
class SpecialCard(Card):
    CLIMATE_ALERT = "ALERT"
    TEAM_COLLAB = "COLLAB"
    ECO_BOOST = "BOOST"

    EFFECT_CHOICES = [
        (CLIMATE_ALERT, "Climate Alert"),
        (TEAM_COLLAB, "Team Collab"),
        (ECO_BOOST, "Eco Boost"),
    ]

    effect = models.CharField(
        max_length=10,
        choices=EFFECT_CHOICES
    )

    def __str__(self):
        return self.get_effect_display()
class PlayerCard(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    part_card = models.ForeignKey(PartCard, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.player.nickname} - {self.part_card.name}"


# @dataclass
# class CardTable:
#     table: dict = None


#     def __init__(self):
#         if self.table == None:
#             self.table = {}
        
#         self.make_table()

#     def make_table(self):
#         OPTICAL = "OPT"
#         MECHANICAL = "MECH"
#         ILLUMINATING = "ILL"

#         CATEGORY_CHOICES = [
#             (OPTICAL, "Optical"),
#             (MECHANICAL, "Mechanical"),
#             (ILLUMINATING, "Illuminating"),
#         ]

#         self.table['part_cards'] = {}
#         part_cards = self.table['part_cards']

#         for outer, value in CATEGORY_CHOICES:
#             part_cards[outer] = value 

#     def get_value(self, inner, outer):
#         return self.table.get(inner, {}).get(outer)
        
#     pass

# if __name__ == '__main__':
#     OPTICAL = "OPT"
#     MECHANICAL = "MECH"
#     ILLUMINATING = "ILL"

#     CATEGORY_CHOICES = [
#         (OPTICAL, "Optical"),
#         (MECHANICAL, "Mechanical"),
#         (ILLUMINATING, "Illuminating"),
#     ]

#     table = CardTable()
#     assert(table.get('play_cards', OPTICAL))
#     pass