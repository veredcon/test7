import logging
from dataclasses import dataclass
from typing import AsyncGenerator, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_litellm import ChatLiteLLM
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import create_react_agent
from opentelemetry import trace

from tools.invoice_scanner import scan_invoices as _scan_invoices
from tools.summary_generator import generate_summary as _generate_summary
from tools.audit_logger import get_audit_logger

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

SYSTEM_PROMPT = """You are an AI agent that monitors invoice approvals, flags high-value pending invoices over 50K, and generates weekly summaries for the CFO. Help users with their requests."""


@tool
def scan_pending_invoices() -> dict:
    """Scan all pending supplier invoices and return flagged ones exceeding 50K threshold pending more than 3 days."""
    return _scan_invoices()


@tool
def create_weekly_summary(flagged_count: int, total_count: int, scan_date: str) -> str:
    """Generate a narrative weekly summary of the invoice approval backlog for the CFO.
    
    Args:
        flagged_count: Number of flagged invoices.
        total_count: Total pending invoices.
        scan_date: ISO date of the scan.
    """
    result = _scan_invoices()
    return _generate_summary(
        flagged_invoices=result["flagged_invoices"],
        all_invoices=result["all_invoices"],
        scan_date=result["scan_date"],
    )


@dataclass
class AgentResponse:
    status: Literal["input_required", "completed", "error"]
    message: str


class SampleAgent:
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self.llm = ChatLiteLLM(model="sap/anthropic--claude-4.5-sonnet")
        self._tools = [scan_pending_invoices, create_weekly_summary]
        self.graph = create_react_agent(self.llm, tools=self._tools)

    async def stream(self, query: str, context_id: str) -> AsyncGenerator[dict, None]:
        yield {
            "is_task_complete": False,
            "require_user_input": False,
            "content": "Processing...",
        }
        try:
            with tracer.start_as_current_span("agent_stream"):
                messages = [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=query),
                ]
                result = await self.graph.ainvoke({"messages": messages})
                response = result["messages"][-1].content
            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": response,
            }
        except Exception as e:
            logger.exception("Agent stream error")
            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": f"Error: {e}",
            }

    def invoke(self, query: str, context_id: str) -> AgentResponse:
        import asyncio

        try:
            with tracer.start_as_current_span("agent_invoke"):
                messages = [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=query),
                ]
                result = asyncio.run(self.graph.ainvoke({"messages": messages}))
                response = result["messages"][-1].content
            return AgentResponse(status="completed", message=response)
        except Exception as e:
            logger.exception("Agent invoke error")
            return AgentResponse(status="error", message=f"Error: {e}")
