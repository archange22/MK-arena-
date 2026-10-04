"""Behavior and tone stylizer"""
from personality.mood import MoodState

class BehaviorStylizer:
    @staticmethod
    def apply_style(text: str, mood: MoodState) -> str:
        if mood in (MoodState.SARCASTIC, MoodState.COLD):
            return f"❄️ [NOVA Mode Glacial] : {text}"
        elif mood == MoodState.ANNOYED:
            return f"😒 {text}"
        elif mood == MoodState.HAPPY:
            return f"✨ {text} ✨"
        return text
