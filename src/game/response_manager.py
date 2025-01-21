from typing import Callable, List, Dict, Any, TYPE_CHECKING, Optional
from dataclasses import dataclass, field
import asyncio

if TYPE_CHECKING:
    from src.core.player_party import PlayerParty
    from src.core.enemies import EnemyParty


@dataclass
class GameResponse:
    input_type: str = ""
    menu_options: List[str] = field(default_factory=list)
    option_details: List[str] = field(default_factory=list)
    main_text: str = ""
    sub_text: str = ""
    player_party: "PlayerParty" = None
    enemy_party: "EnemyParty" = None
    background_image_url: str = ""
    portrait_image_url: str = ""
    npc_text: str = ""
    player_text: str = ""
    npc_portrait_url: str = ""
    player_portrait_url: str = ""
    turn_order: List[str] = field(default_factory=list)
    character_info: Dict[str, Any] = field(default_factory=dict)
    travel_position: List[int] = field(default_factory=list)
    option_portraits: List[str] = field(default_factory=list)
    movement_text: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_type": self.input_type,
            "menu_options": self.menu_options,
            "option_details": self.option_details,
            "main_text": self.main_text,
            "sub_text": self.sub_text,
            "player_party": (
                self.player_party.to_dict() if self.player_party else {"characters": []}
            ),
            "enemy_party": (
                self.enemy_party.to_dict() if self.enemy_party else {"characters": []}
            ),
            "background_image_url": self.background_image_url,
            "portrait_image_url": self.portrait_image_url,
            "npc_text": self.npc_text,
            "player_text": self.player_text,
            "npc_portrait_url": self.npc_portrait_url,
            "player_portrait_url": self.player_portrait_url,
            "turn_order": [char.to_dict() for char in self.turn_order],
            "character_info": self.character_info,
            "travel_position": self.travel_position,
            "option_portraits": self.option_portraits,
            "movement_text": self.movement_text,
        }


@dataclass
class PlayerResponse:
    response: str = ""


class ResponseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialize()
        return cls._instance

    def initialize(self):
        self.game_response = None
        self.player_response = None
        self.websocket = None
        self.response_event = asyncio.Event()
        self.cached_background_image = None

    def set_websocket(self, websocket):
        self.websocket = websocket

    def set_game_response(self, **kwargs):
        if kwargs.get("background_image_url"):
            self.cached_background_image = kwargs["background_image_url"]
        else:
            kwargs["background_image_url"] = self.cached_background_image
        self.game_response = GameResponse(**kwargs)

    def set_menu_options(self, menu_options: List[str]):
        self.game_response.menu_options = menu_options

    def set_option_details(self, option_details: List[str]):
        self.game_response.option_details = option_details

    def send_game_response(self):
        if self.websocket:
            asyncio.create_task(self.websocket.send_json(self.get_game_response()))

    def set_player_response(self, **kwargs):
        self.player_response = PlayerResponse(**kwargs)
        self.response_event.set()  # Signal that a response is available

    def get_game_response(self) -> Dict[str, Any]:
        return self.game_response.to_dict()

    async def get_player_response(self) -> str:
        await self.response_event.wait()  # Wait for a response to be set
        self.response_event.clear()  # Reset the event for the next response
        response = self.player_response.response
        self.player_response = None
        return response


async def choose_option(
    choices: List[Any],
    prompt: str = "Enter the number of your choice: ",
    formatter: Callable[[Any], str] = str,
    allow_exit: bool = True,
    exit_option: str = "Exit",
    sub_text: str = "",
    input_type: str = "menu",
    background_image_url: str = None,
    portrait_image_url: str = None,
    option_details: List[str] = [],
    option_portraits: List[str] = [],
) -> Optional[Any]:
    rm = ResponseManager()

    formatted_choices = [formatter(choice) for choice in choices]
    if allow_exit:
        formatted_choices.append(exit_option)
        option_details.append("")
    if option_portraits:
        option_portraits.append("")

    rm.set_game_response(
        main_text=prompt,
        sub_text=sub_text,
        menu_options=formatted_choices,
        option_details=option_details,
        input_type=input_type,
        background_image_url=background_image_url,
        portrait_image_url=portrait_image_url,
        option_portraits=option_portraits,
    )
    rm.send_game_response()

    response = await rm.get_player_response()
    # get the index of the response in the formatted_choices list
    index = formatted_choices.index(response)
    if allow_exit and index == len(choices):
        return None
    return choices[index]


async def choose_battle_target(
    target_party, party_type: str, background_image_url: str = None
):
    rm = ResponseManager()
    rm.set_game_response(
        **{
            party_type: target_party,
            "input_type": "battle_target",
            "main_text": "Choose a target:",
            "background_image_url": background_image_url,
        }
    )
    rm.send_game_response()
    choice_name = await rm.get_player_response()
    return next(
        (target for target in target_party.characters if target.name == choice_name),
        None,
    )


async def print_event_text(
    title,
    description="",
    background_image_url: str = None,
    input_type: str = "message",
    portrait_image_url: str = None,
    npc_portrait_url: str = None,
    player_portrait_url: str = None,
):
    rm = ResponseManager()
    if input_type == "conversation":
        rm.set_game_response(
            npc_text=title,
            player_text=description,
            input_type=input_type,
            background_image_url=background_image_url,
            npc_portrait_url=npc_portrait_url,
            player_portrait_url=player_portrait_url,
        )
    else:
        rm.set_game_response(
            main_text=title,
            sub_text=description,
            input_type=input_type,
            background_image_url=background_image_url,
            portrait_image_url=portrait_image_url,
            npc_portrait_url=npc_portrait_url,
        )
    rm.send_game_response()
    await rm.get_player_response()


async def print_character_info_async(character_info: Dict[str, Any]):
    rm = ResponseManager()
    rm.set_game_response(character_info=character_info, input_type="stats_message")
    rm.send_game_response()
    await rm.get_player_response()


async def print_battle_menu(
    player_party,
    enemy_party,
    action_options,
    background_image_url: str = None,
    turn_order: List[str] = None,
):
    active_character = turn_order[0]
    main_text = f"{active_character.name}'s turn..."
    rm = ResponseManager()
    rm.set_game_response(
        main_text=main_text,
        player_party=player_party,
        enemy_party=enemy_party,
        input_type="battle",
        menu_options=action_options,
        background_image_url=background_image_url,
        turn_order=turn_order,
    )
    rm.send_game_response()
    return await rm.get_player_response()
