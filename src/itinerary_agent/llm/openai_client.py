from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


class OpenAIChatClient:
    """LLMClient implementation backed by langchain-openai's ChatOpenAI.
    Reads OPENAI_API_KEY from the environment (ChatOpenAI's default).
    Kept in its own module so the vendor SDK import doesn't leak into the
    provider-agnostic LLMClient seam (see itinerary_agent.llm)."""

    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.0):
        self._chat = ChatOpenAI(model=model, temperature=temperature)

    def complete(self, *, system: str, user: str) -> str:
        response = self._chat.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        return str(response.content)
