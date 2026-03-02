import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import GameRoom, Player, PartCard, PlayerCard
from .utils import (
    draw_function_card,
    is_correct_part,
    handle_correct_play,
    handle_incorrect_play,
    rotate_turn,
    check_win_condition
)
from django.utils import timezone
from datetime import timedelta
class GameConsumer(AsyncWebsocketConsumer):
    # Clean up stale players (not seen for 5+ minutes)
    async def cleanup_stale_players(self):
        from django.db.models import Q
        stale_time = timezone.now() - timedelta(minutes=5)
        await sync_to_async(
            Player.objects.filter(room__code=self.room_code, last_seen__lt=stale_time).delete
        )()
    
    async def connect(self):
        self.room_code = self.scope["url_route"]["kwargs"]["room_code"]
        self.group_name = f"game_{self.room_code}"
        
        # Get player_id from session
        self.player_id = self.scope["session"].get("player_id")
        
        if not self.player_id:
            print("❌ No player_id in session, rejecting connection")
            await self.close()
            return

        # Clean up any stale players before accepting connection
        await self.cleanup_stale_players()

        print(f"🔥 CONNECTING TO GROUP: {self.group_name} (Player {self.player_id})")

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        # Auto-send player list when player joins
        await self.send_player_list()
        await self.send(text_data=json.dumps({
            "type": "hand",
            "cards": [
        {"id": 1, "name": "Oxygen Generator"},
        {"id": 2, "name": "Carbon Filter"},
        {"id": 3, "name": "Wind Turbine"},
    ]
}))
    async def disconnect(self, close_code):
        # Remove player from database when disconnecting
        if self.player_id:
            await sync_to_async(Player.objects.filter(id=self.player_id).delete)()
            # Send updated player list to all remaining players
            await self.send_player_list()
        
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    async def receive(self, text_data):
        # Update last_seen timestamp for this player
        await sync_to_async(
            Player.objects.filter(id=self.player_id).update
        )(last_seen=timezone.now())
        
        data = json.loads(text_data)
        action = data.get("action")

        if action == "play_card":
            await self.play_card(data)
        elif action == "draw_card":
            await self.draw_card(data)
        elif action == "start_game":
            await self.start_game()

    async def play_card(self, data):
        function_card_id = data["function_card_id"]
        part_card_id = data["part_card_id"]

        player = await sync_to_async(Player.objects.get)(id=self.player_id)
        function_card = await sync_to_async(
            lambda: draw_function_card()
        )()
        part_card = await sync_to_async(PartCard.objects.get)(id=part_card_id)

        correct = is_correct_part(function_card, part_card)

        if correct:
            player_card = await sync_to_async(
                PlayerCard.objects.get
            )(player=player, part_card=part_card)

            await sync_to_async(handle_correct_play)(player, player_card)
            result = "correct"
        else:
            await sync_to_async(handle_incorrect_play)(player)
            result = "incorrect"

        await sync_to_async(rotate_turn)(player.room)

        win = await sync_to_async(check_win_condition)(player)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "game_update",
                "player": player.nickname,
                "result": result,
                "accuracy": player.accuracy,
                "win": win
            }
        )
    async def draw_card(self, data):
        player = await sync_to_async(Player.objects.get)(id=self.player_id)

        from .utils import draw_one_part_card
        await sync_to_async(draw_one_part_card)(player)

        await sync_to_async(rotate_turn)(player.room)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "game_update",
                "player": player.nickname,
                "result": "draw"
            }
        )
    async def game_update(self, event):
        await self.send(text_data=json.dumps(event))

    async def system_message(self, event):
        await self.send(text_data=json.dumps({
            "system": event["message"]
        }))

    async def send_player_list(self):
        from .models import Player, GameRoom

        room = await sync_to_async(GameRoom.objects.get)(
        code=self.room_code
    )

        players = await sync_to_async(list)(
        Player.objects.filter(room=room)
        .values("id", "nickname", "is_host")
        )

        await self.channel_layer.group_send(
        self.group_name,
        {
            "type": "player_list",
            "players": players,
        }
    )

    async def player_list(self, event):
        await self.send(text_data=json.dumps({
            "type": "player_list",
            "players": event["players"],
        }))

    async def start_game(self):
        room = await sync_to_async(GameRoom.objects.get)(code=self.room_code)

        if room.is_active:
            return

        from .utils import start_game
        await sync_to_async(start_game)(room)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "game_started"
            }
        )

    async def game_started(self, event):
        await self.send(text_data=json.dumps({
            "type": "game_started"
        }))
