"""Dynamic Mood State Machine"""
from enum import Enum

class MoodState(Enum):
    NORMAL = "NORMAL"
    HAPPY = "HAPPY"
    AMUSED = "AMUSED"
    ANNOYED = "ANNOYED"
    SARCASTIC = "SARCASTIC"
    COLD = "COLD"

class MoodManager:
    def __init__(self):
        self.current_mood = MoodState.NORMAL

    def set_mood(self, mood: MoodState):
        self.current_mood = mood

    def get_mood(self) -> MoodState:
        return self.current_mood
