from django.contrib import admin
from .models import (
    GameRoom,
    Player,
    PartCard,
    FunctionCard,
    SpecialCard,
    PlayerCard
)
@admin.register(GameRoom)
class GameRoomAdmin(admin.ModelAdmin):
    list_display = ("code", "created_at")
    search_fields = ("code",)
@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("nickname", "room", "role", "accuracy", "turns_played", "is_finished")
    list_filter = ("room", "is_host", "is_finished")
    search_fields = ("nickname",)

    def role(self, obj):
        return "Host" if obj.is_host else "Member"
@admin.register(PartCard)
class PartCardAdmin(admin.ModelAdmin):
    list_display = ("name", "category")
    list_filter = ("category",)
    search_fields = ("name",)
@admin.register(FunctionCard)
class FunctionCardAdmin(admin.ModelAdmin):
    list_display = ("short_description", "correct_part", "difficulty")
    list_filter = ("difficulty",)
    search_fields = ("description",)

    def short_description(self, obj):
        return obj.description[:40]
@admin.register(SpecialCard)
class SpecialCardAdmin(admin.ModelAdmin):
    list_display = ("name", "effect")
    list_filter = ("effect",)
@admin.register(PlayerCard)
class PlayerCardAdmin(admin.ModelAdmin):
    list_display = ("player", "part_card", "room")
    list_filter = ("player",)
