from typing import Literal

Slot = Literal["breakfast", "morning", "lunch", "afternoon", "dinner", "evening"]

SLOT_NAMES: tuple[Slot, ...] = ("breakfast", "morning", "lunch", "afternoon", "dinner", "evening")
ACTIVITY_SLOTS: tuple[Slot, ...] = ("morning", "afternoon", "evening")
MEAL_SLOTS: tuple[Slot, ...] = ("breakfast", "lunch", "dinner")
