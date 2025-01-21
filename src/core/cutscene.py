from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING
from src.api.llm import get_llm
from src.game.response_manager import print_event_text
from src.npc.cast import get_cast
from src.api.images import generate_npc_portrait

if TYPE_CHECKING:
    from src.core.story import StoryEvent
    from src.npc.cast import CastManager


async def cutscene(
    event: StoryEvent,
    location_name: str,
    location_description: str,
    scene_npcs: List[str],
    background_image_url: Optional[str] = None,
    past_events: Optional[List[StoryEvent]] = None,
    thematic_style: Optional[str] = None,
    conversation_length: str = "short",
    event_timing: str = "during_event",
):
    narrative = get_llm().generate_cutscene(
        event_description=event.event_text,
        characters=scene_npcs,
        location_name=location_name,
        location_description=location_description,
        past_events=[e.event_text for e in past_events] if past_events else [],
        story_level=len(past_events) if past_events else 0,
        thematic_style=thematic_style,
        conversation_length=conversation_length,
        event_timing=event_timing,
    )
    # check if any new npcs are in the narrative
    for scene in narrative["scene"]:
        if (
            scene["type"] == "dialogue"
            and get_cast().get_npc_by_name(scene["speaker"]) is None
        ):
            get_cast().make_new_npc(
                scene["speaker"], scene["text"], location_name, location_description
            )
    await run_dialogue(narrative, background_image_url)
    return narrative["scene"]


async def run_dialogue(narrative: dict, background_image_url: str):
    # Display the narrative scenes
    for scene in narrative["scene"]:
        if scene["type"] == "dialogue":
            character = get_cast().get_npc_by_name(scene["speaker"])
            portrait = character.portrait if character else None
            await print_event_text(
                scene["speaker"],
                f'"{scene["text"]}"',
                background_image_url,
                portrait_image_url=portrait,
                input_type="dialogue",
            )
        elif scene["type"] == "narration":
            await print_event_text("", scene["text"], background_image_url)
        else:
            pass
