from src.npc.npc import NPC
from src.core.enemies import make_enemy, EnemyParty
from src.battle.battle import Battle
from src.game.response_manager import print_event_text
from src.battle.effects import Intimidated


class BossNPC(NPC):
    def __init__(self, boss_data, current_location, story_level):
        boss_data = boss_data.copy()
        boss_data["type"] = "boss"
        super().__init__(
            boss_data,
            current_location,
            story_level=story_level + 5,
        )
        self.defeated = False

    async def confront(self, party, intimidated: bool = False):
        boss_enemy = make_enemy(
            location_dict={
                "name": self.current_location,
                "description": "",
            },
            level=self.story_level,
            is_boss=True,
            enemy_info={"name": self.name, "description": self.description},
            portrait=self.portrait,
        )

        if intimidated:
            await Intimidated().apply(boss_enemy)

        battle = Battle(party, EnemyParty([boss_enemy]), context="boss_encounter")
        battle_result = await battle.start(battle_type="boss_battle")

        if battle_result == "party_victory":
            return await self.confront_success(party)
        elif battle_result == "party_defeated":
            return await self.confront_failure(party)
        elif battle_result == "party_ran":
            await print_event_text(
                "Boss Battle",
                "You decide to turn back and prepare more before facing the boss.",
            )
            return "ran"

    async def confront_success(self, party):
        self.defeated = True

        event_info = {
            "location": self.current_location,
            "event_text": f"{self.name} has been defeated!",
            "trigger": {"type": "boss_defeated", "value": self.name},
        }
        party.story_manager.add_past_event(event_info)
        return "victory"

    async def confront_failure(self, party):
        await print_event_text(
            "Game Over",
            "Your party has been defeated...",
            portrait_image_url=self.portrait,
        )
        return "defeated"
