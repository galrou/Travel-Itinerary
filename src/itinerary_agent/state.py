from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

from itinerary_agent.domain import Activity, Day, Location, Requirements, Restaurant, Trip


class ConversationState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    requirements: Requirements
    candidates: list[Activity]
    anchor: Location | None
    day: Day | None
    restaurant_candidates: list[Restaurant]
    trip: Trip | None
