from pydantic import BaseModel, Field

from application.dtos.game_state_event import GameStateGroupGameEvent
from application.models import ModelID


class Trait(BaseModel):
    name: str = Field(..., alias="name")
    value: float = Field(..., alias="value")

    def __str__(self):
        return f"{self.value}% {self.name}"

    def __repr__(self):
        return self.__str__()


class InitPrompts(BaseModel):
    traits: list[Trait] = Field(..., alias="traits")

    def to_list(self):
        event_sample = GameStateGroupGameEvent.sample()
        return [
            (
                "Imagine you're commenting the battle royale game match. You'll be getting lists of game state events like this one: "
                f"{event_sample.model_dump()} "
                "Try to see the changes in the game state and comment on them. "
                "Requirement 1: you need to use 3 senteces max. "
                "Requirement 2: You're not supposed to always use each field for the comment, but you can use them if you think they're relevant. "
                "Requirement 3: You will also get some events which haven't happened in the game yet, you can take them into consideration but "
                "YOU CAN'T MENTION THAT YOU HAVE INFO FROM THE FUTURE UNDER NO CIRCUMSTANCES, ONLY USE IT TO ADJUST YOUR SENTIMENT IN COMMENTING ON CURRENT EVENTS. "
                "Requirement 4: You need to adjust the commentary sentiment. "
                f"Show {', '.join(str(trait) for trait in self.traits)} in your comments. "
                "Understood?"
            ),
            "Understood. I'm ready to commentate on the battle royale game events with given character settings.",
        ]


class AgentServiceConfig(BaseModel):
    init_prompts: InitPrompts = Field(...)
    past_window_size_sec: int = Field(default=5)
    future_window_size_sec: int = Field(default=3)
    game_start_timestamp: int = Field(...)
    model_id: ModelID = Field(default=ModelID.NOVA_PRO)
    context_window_size: int = Field(default=20)
    temperature: float = Field(default=0.9)

    def model_dump(self, *args, **kwargs):
        dump = super().model_dump(*args, **kwargs)
        del dump["init_prompts"]
        dump["traits"] = self.init_prompts.traits
        return dump
