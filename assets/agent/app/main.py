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
from opentelemetry import trace
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from sap_cloud_sdk.extensibility import build_extension_capabilities

from agent_executor import AgentExecutor
from extension_capabilities import EXTENSION_CAPABILITIES
from tools.audit_logger import get_audit_logger
from tools.invoice_scanner import scan_invoices
from tools.summary_generator import generate_summary

from pythonjsonlogger.json import JsonFormatter
from extension_telemetry.log_filter import ExtensionContextLogFilter

# Structured JSON logging so Kyma's log pipeline can parse extension attributes
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
json_formatter = JsonFormatter(
    fmt="%(levelname)s %(name)s %(message)s",
    rename_fields={"levelname": "level"},
)
json_handler = logging.StreamHandler()
json_handler.setFormatter(json_formatter)
json_handler.addFilter(ExtensionContextLogFilter())
root_logger.addHandler(json_handler)

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))


async def weekly_summary_handler(request: Request) -> JSONResponse:
    """
    GET /weekly-summary
    Scans invoices, flags high-value ones, generates LLM summary, logs audit entry,
    and returns a JSON response for the CFO.
    """
    with tracer.start_as_current_span("weekly_summary_endpoint") as span:
        audit = get_audit_logger()
        reason = None
        try:
            # Step 1 & 2: Scan + flag invoices
            scan_result = scan_invoices()
            flagged = scan_result["flagged_invoices"]
            all_invoices = scan_result["all_invoices"]
            scan_date = scan_result["scan_date"]

            # Log each flagged invoice to audit log
            for inv in flagged:
                audit.log_flag(
                    invoice_id=inv["SupplierInvoice"],
                    amount=inv["InvoiceGrossAmount"],
                    action="flagged",
                )

            # Step 3: Generate summary
            summary = generate_summary(
                flagged_invoices=flagged,
                all_invoices=all_invoices,
                scan_date=scan_date,
            )

            # Step 4: Log notification dispatch
            audit.log_notification(action="notification_dispatched")

            logger.info("M4.achieved: CFO notification sent via n8n workflow")
            span.set_attribute("endpoint.status", "success")
            span.set_attribute("endpoint.flagged_count", len(flagged))

            return JSONResponse(
                content={
                    "flagged_invoices": flagged,
                    "summary": summary,
                    "audit_log": audit.get_log(),
                    "scan_date": scan_date,
                },
                status_code=200,
            )

        except Exception as e:
            reason = str(e)
            logger.warning(f"M4.missed: CFO notification failed - {reason}")
            span.record_exception(e)
            span.set_attribute("endpoint.status", "error")
            return JSONResponse(
                content={"error": f"Weekly summary generation failed: {reason}"},
                status_code=500,
            )


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
    weekly_summary_skill = AgentSkill(
        id="weekly-summary",
        name="weekly-summary",
        description="Generate a weekly summary of flagged high-value pending invoices for the CFO",
        tags=["invoice", "summary", "weekly", "cfo"],
        examples=["Generate weekly summary"],
    )
    agent_card = AgentCard(
        name="invoice-approval-monitor-agent",
        description="An AI agent that monitors invoice approvals, flags high-value pending invoices over 50K, and generates weekly summaries for the CFO",
        url=os.environ.get("AGENT_PUBLIC_URL", f"http://{host}:{port}/"),
        version="1.0.0",
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
        capabilities=AgentCapabilities(
            streaming=True,
            pushNotifications=False,
            extensions=build_extension_capabilities(EXTENSION_CAPABILITIES),
        ),
        skills=[skill, weekly_summary_skill],
    )

    a2a_app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=DefaultRequestHandler(
            agent_executor=AgentExecutor(),
            task_store=InMemoryTaskStore(),
        ),
    )

    # Build combined Starlette app with A2A routes + custom /weekly-summary
    a2a_built = a2a_app.build()
    combined_routes = list(a2a_built.routes) + [
        Route("/weekly-summary", endpoint=weekly_summary_handler, methods=["GET"]),
    ]
    app = Starlette(routes=combined_routes)

    logger.info(f"Starting Invoice Approval Monitor Agent at http://{host}:{port}")
    logger.info(f"Weekly summary endpoint: http://{host}:{port}/weekly-summary")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
