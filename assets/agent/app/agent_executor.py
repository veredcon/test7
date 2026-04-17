import logging
import uuid

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    InternalError,
    Message,
    Part,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import new_agent_text_message, new_task
from a2a.utils.errors import ServerError
from a2a.utils.message import get_message_text
from sap_cloud_sdk.extensibility import (
    HookType,
    OnFailure,
    create_client,
    get_extension_override,
)
from sap_cloud_sdk.extensibility.exceptions import TransportError

from agent import SampleAgent
from extension_telemetry import emit_extensions_summary_span

logger = logging.getLogger(__name__)

# Create extensibility client once at startup
extensibility_client = create_client()


class AgentExecutor(AgentExecutor):
    def __init__(self):
        self.agent = SampleAgent()
        self.extensibility_client = extensibility_client

    async def _run_hooks(
        self,
        hooks: list,
        hook_type: HookType,
        message: Message,
        updater: TaskUpdater,
        task,
        ext_impl=None,
    ) -> float:
        """Run all hooks of the given type against *message*.

        Appends hook-contributed parts to *message* in place.
        Returns total wall-clock duration (seconds) of all hook calls executed.
        """
        import time

        from opentelemetry import trace
        from sap_cloud_sdk.core.telemetry import ExtensionType, extension_context

        _tracer = trace.get_tracer("sap.cloud_sdk.extension")

        filtered = [h for h in hooks if h.type == hook_type]
        phase = "pre" if hook_type == HookType.BEFORE else "post"
        logger.info("Found %d %s-execution hook(s)", len(filtered), phase)

        total_duration = 0.0

        for hook in filtered:
            hook_name = hook.name or hook.id or "unknown"
            await updater.update_status(
                TaskState.working,
                new_agent_text_message(
                    f"Executing {phase}-execution hook: {hook_name}",
                    task.context_id,
                    task.id,
                ),
            )

            source_info = None
            if ext_impl and ext_impl.source:
                source_info = ext_impl.get_source_info_for_hook(hook.ord_id)
            resolved_name = (
                source_info.extension_name
                if source_info
                else (ext_impl.extension_name if ext_impl else "unknown")
            )
            resolved_id = source_info.extension_id if source_info else ""
            resolved_version = source_info.extension_version if source_info else ""
            capability = "default"

            t0 = time.monotonic()
            try:
                with (
                    extension_context(
                        capability_id=capability,
                        extension_name=resolved_name,
                        extension_type=ExtensionType.HOOK,
                        extension_id=resolved_id,
                        extension_version=resolved_version,
                        item_name=hook_name,
                    ),
                    _tracer.start_as_current_span(
                        f"extension_hook {hook_name}",
                        attributes={
                            "sap.extension.isExtension": True,
                            "sap.extension.extensionType": ExtensionType.HOOK.value,
                            "sap.extension.capabilityId": capability,
                            "sap.extension.extensionId": resolved_id,
                            "sap.extension.extensionName": resolved_name,
                            "sap.extension.extensionVersion": resolved_version,
                            "sap.extension.extension.item.name": hook_name,
                        },
                    ),
                ):
                    response = self.extensibility_client.call_hook(hook, message)
                    if response is not None:
                        logger.info("Hook '%s' returned a response", hook_name)
                        await updater.update_status(
                            TaskState.working,
                            new_agent_text_message(
                                f"Processing {hook_name} response…",
                                task.context_id,
                                task.id,
                            ),
                        )
                        metadata = response.metadata or {}
                        if metadata.get("stop_execution"):
                            if hook.can_short_circuit:
                                stop_reason = metadata.get("stop_execution_reason") or (
                                    f"Hook '{hook_name}' blocked execution."
                                )
                                logger.warning(
                                    "Hook '%s' blocked execution: %s",
                                    hook_name,
                                    stop_reason,
                                )
                                raise ServerError(InternalError(message=stop_reason))
                            else:
                                logger.info(
                                    "Hook '%s' signalled stop_execution but canShortCircuit=false — ignoring",
                                    hook_name,
                                )
                        if response.parts:
                            message.parts.extend(response.parts)
                            logger.info(
                                "Hook '%s' appended %d part(s)",
                                hook_name,
                                len(response.parts),
                            )
            except TransportError as e:
                logger.error("Error calling hook '%s': %s", hook_name, e)
                if hook.on_failure == OnFailure.BLOCK:
                    raise ServerError(
                        InternalError(message=f"Hook '{hook_name}' failed: {e}")
                    )
            finally:
                total_duration += time.monotonic() - t0

        return total_duration

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        try:
            incoming_message = context.message
            query = context.get_user_input()

            task = context.current_task
            is_new_task = task is None
            if not task:
                task = new_task(context.message)
                await event_queue.enqueue_event(task)

            updater = TaskUpdater(event_queue, task.id, task.context_id)

            # Fetch extension capability implementation
            override = get_extension_override(context)
            ext_impl = self.extensibility_client.get_extension_capability_implementation(
                capability_id="default",
                override=override,
            )

            total_ext_duration = 0.0
            hook_call_count = 0

            # BEFORE hooks — only for new tasks
            if not is_new_task:
                logger.info("Skipping pre-execution hooks — ongoing task %s", task.id)
            else:
                pre_hooks = [h for h in ext_impl.hooks if h.type == HookType.BEFORE]
                hook_call_count += len(pre_hooks)
                pre_duration = await self._run_hooks(
                    ext_impl.hooks,
                    HookType.BEFORE,
                    incoming_message,
                    updater,
                    task,
                    ext_impl=ext_impl,
                )
                total_ext_duration += pre_duration

            # Inject extension instruction into query if available
            effective_query = get_message_text(incoming_message) or query
            if ext_impl.instruction:
                effective_query = f"{ext_impl.instruction}\n\n{effective_query}"

            async for item in self.agent.stream(effective_query, task.context_id):
                if not item["is_task_complete"] and not item["require_user_input"]:
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(
                            item["content"], task.context_id, task.id
                        ),
                    )
                elif item["require_user_input"]:
                    await updater.update_status(
                        TaskState.input_required,
                        new_agent_text_message(
                            item["content"], task.context_id, task.id
                        ),
                        final=True,
                    )
                    break
                else:
                    # Build result message for AFTER hooks
                    agent_result_message = Message(
                        message_id=str(uuid.uuid4()),
                        context_id=task.context_id,
                        role="agent",
                        kind="message",
                        parts=[
                            *incoming_message.parts,
                            Part(root=TextPart(kind="text", text=item["content"])),
                        ],
                    )

                    post_hooks = [h for h in ext_impl.hooks if h.type == HookType.AFTER]
                    hook_call_count += len(post_hooks)
                    post_duration = await self._run_hooks(
                        ext_impl.hooks,
                        HookType.AFTER,
                        agent_result_message,
                        updater,
                        task,
                        ext_impl=ext_impl,
                    )
                    total_ext_duration += post_duration

                    tool_call_count = sum(
                        len(s.tool_names or []) for s in ext_impl.mcp_servers
                    )
                    emit_extensions_summary_span(
                        tool_call_count=tool_call_count,
                        hook_call_count=hook_call_count,
                        has_instruction=ext_impl.instruction is not None,
                        total_duration_ms=total_ext_duration * 1000,
                    )

                    final_text_parts = [
                        p.root
                        for p in agent_result_message.parts
                        if isinstance(p.root, TextPart)
                    ]
                    final_text = (
                        final_text_parts[-1].text
                        if final_text_parts
                        else item["content"]
                    )
                    await updater.add_artifact(
                        [Part(root=TextPart(text=final_text))], name="agent_result"
                    )
                    await updater.complete()
                    break

        except ServerError:
            raise
        except Exception as e:
            logger.exception("Agent execution error")
            raise ServerError(error=InternalError()) from e

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise ServerError(error=UnsupportedOperationError())
