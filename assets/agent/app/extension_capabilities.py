"""Extension capability definitions for agent extensibility.

This module defines the extension capability that allows customers to extend
this agent with additional tools, instructions, and hooks.

The EXTENSION_CAPABILITIES list is used to build A2A AgentExtension objects
that are included in the agent card's capabilities.
"""

from sap_cloud_sdk.extensibility import (
    ExtensionCapability,
    HookCapability,
    HookType,
    ToolAdditions,
    Tools,
)

# Hooks available for this agent extension.
PRE_HOOK = HookCapability(
    type=HookType.BEFORE,
    id="agent_pre_hook",
    display_name="Before Hook",
    description="Executed before the main invoice monitoring agent logic runs.",
)

POST_HOOK = HookCapability(
    type=HookType.AFTER,
    id="agent_post_hook",
    display_name="After Hook",
    description="Executed after the main invoice monitoring agent logic runs.",
)

# Extension capability definition for this agent
EXTENSION_CAPABILITIES: list[ExtensionCapability] = [
    ExtensionCapability(
        display_name="Default",
        description=(
            "Extend the Invoice Approval Monitor Agent with custom invoice scanning rules, "
            "additional data sources, custom notification channels, or specialized "
            "audit logging integrations."
        ),
        instruction_supported=True,
        tools=Tools(additions=ToolAdditions(enabled=True)),
        supported_hooks=[PRE_HOOK, POST_HOOK],
    ),
]
