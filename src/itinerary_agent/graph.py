from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from itinerary_agent.config import AllowedDomainsList
from itinerary_agent.constants import (
    NODE_FINALIZE,
    NODE_REQUIREMENTS,
    NODE_RESEARCH,
    NODE_RESTAURANT_RESEARCH,
    NODE_RESTAURANT_SELECTION,
    NODE_SEQUENCE,
    ROUTE_END,
)
from itinerary_agent.llm import ActivityResearcher, RequirementsExtractor, RestaurantResearcher
from itinerary_agent.nodes import ActivityNodes, IntakeNodes, RestaurantNodes, finalize
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
    intake = IntakeNodes(extractor=extractor)
    activities = ActivityNodes(activity_researcher=activity_researcher, allowed_domains=allowed_domains)
    restaurants = RestaurantNodes(restaurant_researcher=restaurant_researcher, allowed_domains=allowed_domains)
    graph = StateGraph(ConversationState)

    graph.add_node(NODE_REQUIREMENTS, intake.requirements)
    graph.add_node(NODE_RESEARCH, activities.research)
    graph.add_node(NODE_SEQUENCE, activities.sequence)
    graph.add_node(NODE_RESTAURANT_RESEARCH, restaurants.restaurant_research)
    graph.add_node(NODE_RESTAURANT_SELECTION, restaurants.restaurant_selection)
    graph.add_node(NODE_FINALIZE, finalize)

    graph.add_edge(START, NODE_REQUIREMENTS)
    graph.add_conditional_edges(
        NODE_REQUIREMENTS,
        intake.route_after_requirements,
        {NODE_RESEARCH: NODE_RESEARCH, ROUTE_END: END},
    )
    graph.add_edge(NODE_RESEARCH, NODE_SEQUENCE)
    graph.add_edge(NODE_SEQUENCE, NODE_RESTAURANT_RESEARCH)
    graph.add_edge(NODE_RESTAURANT_RESEARCH, NODE_RESTAURANT_SELECTION)
    graph.add_edge(NODE_RESTAURANT_SELECTION, NODE_FINALIZE)
    graph.add_edge(NODE_FINALIZE, END)

    return graph.compile(checkpointer=checkpointer)
