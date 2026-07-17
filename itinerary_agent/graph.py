from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from itinerary_agent.extraction import RequirementsExtractor
from itinerary_agent.nodes import (
    make_finalize_node,
    make_requirements_node,
    make_research_node,
    make_restaurant_research_node,
    make_restaurant_selection_node,
    make_sequencing_node,
    route_after_requirements,
)
from itinerary_agent.research import ActivityResearcher, RestaurantResearcher
from itinerary_agent.sources import AllowedDomainsList
from itinerary_agent.state import ConversationState


def build_graph(
    extractor: RequirementsExtractor,
    activity_researcher: ActivityResearcher,
    restaurant_researcher: RestaurantResearcher,
    allowed_domains: AllowedDomainsList,
    checkpointer: BaseCheckpointSaver,
) -> CompiledStateGraph:
    """Composes the Requirements / Research / Sequencing / Restaurant nodes
    into the single-Leg, single-Day itinerary graph (LangGraph state machine,
    built by injecting collaborators rather than subclassing node base
    classes)."""
    graph = StateGraph(ConversationState)

    graph.add_node("requirements", make_requirements_node(extractor))
    graph.add_node("research", make_research_node(activity_researcher, allowed_domains))
    graph.add_node("sequence", make_sequencing_node())
    graph.add_node("restaurant_research", make_restaurant_research_node(restaurant_researcher, allowed_domains))
    graph.add_node("restaurant_selection", make_restaurant_selection_node())
    graph.add_node("finalize", make_finalize_node())

    graph.add_edge(START, "requirements")
    graph.add_conditional_edges(
        "requirements",
        route_after_requirements,
        {"research": "research", "end": END},
    )
    graph.add_edge("research", "sequence")
    graph.add_edge("sequence", "restaurant_research")
    graph.add_edge("restaurant_research", "restaurant_selection")
    graph.add_edge("restaurant_selection", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile(checkpointer=checkpointer)
