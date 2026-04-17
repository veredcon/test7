# CRITICAL: Initialize telemetry BEFORE importing AI frameworks
from sap_cloud_sdk.aicore import set_aicore_config
from sap_cloud_sdk.core.telemetry import auto_instrument

set_aicore_config()
auto_instrument()

import logging
import os

import click
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from agent_executor import AgentExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))


@click.command()
@click.option("--host", default=HOST)
@click.option("--port", default=PORT)
def main(host: str, port: int):
    skill = AgentSkill(
        id="invoice-approval-monitor-agent",
        name="invoice-approval-monitor-agent",
        description="An AI agent that monitors invoice approvals, flags high-value pending invoices over 50K, and generates weekly summaries for the CFO",
        tags=["invoice", "approval", "monitor", "finance", "agent"],
        examples=["Show me flagged invoices this week", "Generate the weekly invoice summary for the CFO"],
    )
    agent_card = AgentCard(
        name="invoice-approval-monitor-agent",
        description="An AI agent that monitors invoice approvals, flags high-value pending invoices over 50K, and generates weekly summaries for the CFO",
        url=os.environ.get("AGENT_PUBLIC_URL", f"http://{host}:{port}/"),
        version="1.0.0",
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
        capabilities=AgentCapabilities(streaming=True, pushNotifications=False),
        skills=[skill],
    )
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=DefaultRequestHandler(
            agent_executor=AgentExecutor(),
            task_store=InMemoryTaskStore(),
        ),
    )
    logger.info(f"Starting A2A server at http://{host}:{port}")
    uvicorn.run(server.build(), host=host, port=port)


if __name__ == "__main__":
    main()
