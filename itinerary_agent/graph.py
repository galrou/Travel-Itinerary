from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from itinerary_agent.extraction import RequirementsExtractor
from itinerary_agent.nodes import (
    make_requirements_node,
    make_research_node,
    make_sequencing_node,
    route_after_requirements,
)
from itinerary_agent.research import ActivityResearcher
from itinerary_agent.sources import AllowedDomainsList
from itinerary_agent.state import ConversationState


def build_graph(
    extractor: RequirementsExtractor,
    researcher: ActivityResearcher,
    allowed_domains: AllowedDomainsList,
    checkpointer: BaseCheckpointSaver,
) -> CompiledStateGraph:
    """Composes the Requirements / Research / Sequencing nodes into the
    single-Leg, single-Day itinerary graph (LangGraph state machine, built by
    injecting collaborators rather than subclassing node base classes)."""
    graph = StateGraph(ConversationState)

    graph.add_node("requirements", make_requirements_node(extractor))
    graph.add_node("research", make_research_node(researcher, allowed_domains))
    graph.add_node("sequence", make_sequencing_node())

    graph.add_edge(START, "requirements")
    graph.add_conditional_edges(
        "requirements",
        route_after_requirements,
        {"research": "research", "end": END},
    )
    graph.add_edge("research", "sequence")
    graph.add_edge("sequence", END)

    return graph.compile(checkpointer=checkpointer)
