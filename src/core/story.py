from dataclasses import dataclass
from typing import List, Optional, Dict
from enum import Enum
from src.game.response_manager import print_event_text
from src.api.llm import get_llm
from src.npc.cast import get_cast
from src.core.cutscene import cutscene
from src.core.party import Party


class TriggerType(Enum):
    LOCATION = "location_entered"
    LANDMARK = "landmark_inspected"
    STORY = "story_exposition"
    BOSS = "boss_confronted"
    ALLY = "ally_recruited"


@dataclass(frozen=False)
class StoryEvent:
    """Represents a single story event with location, content, trigger, and completion status."""

    location: str
    event_text: str
    trigger: Dict[str, str]  # {"type": str, "value": str}
    completed: bool = False
    trigger_hint: str = None

    def to_dict(self) -> dict:
        """Convert the StoryEvent to a dictionary for JSON serialization."""
        return {
            "location": self.location,
            "event_text": self.event_text,
            "trigger": self.trigger,
            "completed": self.completed,
            "trigger_hint": self.trigger_hint,
        }


class StoryManager:
    """Manages a sequence of story events and their progression."""

    def __init__(
        self, thematic_style: Optional[str] = "", currency_name: Optional[str] = "Gold"
    ):
        self.past_events: List[StoryEvent] = []
        self.future_events: List[StoryEvent] = []
        self._story_so_far_cache: Optional[str] = None
        self._last_cached_event_count: int = 0
        self.thematic_style = thematic_style
        self.currency_name = currency_name
        self.chapter_overviews: List[Dict] = []
        self.current_chapter: int = 0
        self.total_chapters: int = 5
        self.current_sub_chapter: int = 0

    def advance_chapter(self) -> None:
        self.current_chapter += 1
        self.current_sub_chapter = 0

    @property
    def next_event(self) -> Optional[StoryEvent]:
        """Get the current active event, or None if all events are completed."""
        return self.future_events[0] if self.future_events else None

    def add_future_event(self, event_dict: dict) -> None:
        """Add a new story event to the sequence."""
        self.future_events.append(StoryEvent(**event_dict))

    def add_past_event(self, event_dict: dict) -> None:
        """Add a new story event to the sequence."""
        self.past_events.append(StoryEvent(**event_dict))

    def add_chapter_overview(self, chapter_overview: Dict) -> None:
        """Add a new chapter overview to the sequence."""
        self.chapter_overviews.append(chapter_overview)

    def generate_sub_chapter_events(self) -> List[StoryEvent]:
        """Generate a list of new story events for a sub-chapter."""
        # Get the sub-chapter from the chapter overviews based on the location
        sub_chapter = self.chapter_overviews[self.current_chapter]["sub_chapters"][
            self.current_sub_chapter
        ]
        story_events = get_llm().generate_sub_chapter_events(
            chapter_title=sub_chapter["chapter_title"],
            chapter_overview=sub_chapter["chapter_overview"],
            sub_chapter_overview=sub_chapter["overview"],
            location=sub_chapter["location"],
            available_npc=sub_chapter["npc"],
            available_landmark=sub_chapter["landmark"],
            previous_events=[],
        )
        sub_chapter["events"] = story_events["events"]
        self.add_sub_chapter_events(sub_chapter)

    def add_sub_chapter_events(self, sub_chapter: dict) -> None:
        """Add a list of new story events to the sequence."""
        story_events = []
        for event_dict in sub_chapter["events"]:
            use_location = sub_chapter["location"].copy()
            event = StoryEvent(
                location=use_location,
                event_text=event_dict["event_text"],
                trigger=event_dict["trigger"],
                completed=False,
                trigger_hint=event_dict["trigger_hint"],
            )
            story_events.append(event)
        self.future_events.extend(story_events)

    async def check_trigger(self, trigger_type: TriggerType, value: str) -> bool:
        """Generic method to check any type of trigger."""
        if not self.next_event:
            return False

        # Check if the trigger type and value match the next event's trigger
        if (
            self.next_event.trigger["type"] == trigger_type.value
            and self.next_event.trigger["value"].lower() == value.lower()
        ):
            return True
        return False

    async def check_location_trigger(self, location: str, part: str) -> bool:
        # first check if it is part A
        if part == "A":
            location = location.split(" (")[0]
            return await self.check_trigger(TriggerType.LOCATION, location)
        else:
            return False

    async def check_landmark_trigger(self, landmark_name: str) -> bool:
        return await self.check_trigger(TriggerType.LANDMARK, landmark_name)

    async def check_npc_trigger(self, npc_name: str, npc_type: str, part: str) -> bool:
        if part == "A":
            return False
        if npc_type == "boss":
            is_boss = await self.check_boss_trigger(npc_name)
            if is_boss:
                return True
            else:
                return await self.check_trigger(TriggerType.STORY, npc_name)
        elif npc_type == "ally":
            is_ally = await self.check_ally_trigger(npc_name)
            if is_ally:
                return True
            else:
                return await self.check_trigger(TriggerType.STORY, npc_name)
        else:
            return await self.check_trigger(TriggerType.STORY, npc_name)

    async def check_boss_trigger(self, boss: str) -> bool:
        return await self.check_trigger(TriggerType.BOSS, boss)

    async def check_ally_trigger(self, ally: str) -> bool:
        return await self.check_trigger(TriggerType.ALLY, ally)

    async def trigger_event(
        self,
        event: StoryEvent,
        location_name: str,
        location_description: str,
        background_image_url: Optional[str] = None,
        player_party: Optional[Party] = None,
    ) -> None:
        """
        Trigger a story event and display its narrative content.

        Args:
            event: The story event to trigger
            location_name: Name of the current location
            location_description: Description of the current location
            background_image_url: Optional URL for background image
            trigger_npc: Optional name of NPC that triggered this event
        """
        npcs = get_cast()

        # Get all relevant NPCs for this scene
        scene_npcs = [
            f"{char.name} (ALLY - {char.description})"
            for char in player_party.characters
        ]
        trigger_type = event.trigger["type"]
        trigger_value = event.trigger["value"]
        if (
            trigger_type == TriggerType.STORY.value
            or trigger_type == TriggerType.ALLY.value
            or trigger_type == TriggerType.BOSS.value
        ):
            trigger_npc_obj = npcs.get_npc_by_name(trigger_value)
            if trigger_npc_obj and trigger_npc_obj.name not in scene_npcs:
                scene_npcs.append(
                    f"{trigger_npc_obj.name} ({trigger_npc_obj.type} - {trigger_npc_obj.description})"
                )

        if (
            trigger_type == TriggerType.ALLY.value
            or trigger_type == TriggerType.BOSS.value
        ):
            event_timing = "before_event"
        else:
            event_timing = "during_event"

        dialogue = await cutscene(
            event,
            location_name,
            location_description,
            scene_npcs,
            background_image_url,
            past_events=self.past_events,
            thematic_style=self.thematic_style,
            event_timing=event_timing,
            conversation_length="short" if event_timing == "before_event" else "long",
        )

        if (
            trigger_type == TriggerType.ALLY.value
            or trigger_type == TriggerType.BOSS.value
        ):
            if trigger_npc_obj and trigger_npc_obj.type == "ally":
                result = await trigger_npc_obj.recruit(player_party, dialogue)
                if result == "recruit_success":
                    pass
                elif result == "recruit_failure":
                    return
            elif trigger_npc_obj and trigger_npc_obj.type == "boss":
                result = await trigger_npc_obj.confront(player_party, False)
                if result == "victory":
                    pass
                elif result == "defeated":
                    return "game_over"
                elif result == "ran":
                    return

            dialogue = await cutscene(
                event,
                location_name,
                location_description,
                scene_npcs,
                background_image_url,
                past_events=self.past_events,
                thematic_style=self.thematic_style,
                event_timing="after_event",
                conversation_length="short",
            )

        event.completed = True
        self.past_events.append(self.future_events.pop(0))

    async def get_story_so_far(self) -> None:
        """Generate and display a summary of the story so far."""
        current_event_count = len(self.past_events)

        # Use cached summary if available and still valid
        if (
            self._story_so_far_cache
            and current_event_count == self._last_cached_event_count
        ):
            summary = self._story_so_far_cache
        # Use default message for new games
        elif not self.past_events:
            summary = "Your journey has just begun..."
        # Generate new summary
        else:
            story_summary = get_llm().generate_story_so_far(
                past_events=[e.to_dict() for e in self.past_events],
                thematic_style=self.thematic_style,
            )
            summary = story_summary["summary"]
            self._story_so_far_cache = summary
            self._last_cached_event_count = current_event_count

        await print_event_text("The Story So Far", summary)
