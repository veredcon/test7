# Invoice Approval Monitor Agent

An AI agent that monitors invoice approvals, flags high-value pending invoices over 50K, and generates weekly summaries for the CFO

## Overview

Uses A2A Protocol, LangGraph, LiteLLM, and Application Foundation SDK.

## Structure

- `Dockerfile` - Container build
- `app/main.py` - A2A server entry
- `app/agent_executor.py` - Request handling
- `app/agent.py` - Agent logic

## Local Development

Requires SAP Artifactory credentials. Use `appfnd-agent-run-local` skill for instructions.
