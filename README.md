# sre-runbook-api

Centralized SRE runbook API for service alerts, operational metadata, remediation references, and incident context.

## Overview

`sre-runbook-api` is a production-oriented backend service for centralizing operational knowledge used during incident response and on-call workflows. It is designed to provide a reliable, structured foundation for storing and retrieving runbooks, alert context, and remediation guidance.

## Features

- Centralized storage for service runbooks and incident response references.
- Structured access to alert context and operational metadata.
- API-first design for SRE and platform workflows.
- Built to support production-style incident response processes.

## Architecture

The service is designed as a focused backend API with clear separation between operational data, incident context, and remediation references. The goal is to keep the domain model simple, maintainable, and easy to extend as the project grows.

## Tech Stack

- FastAPI.
- Python.
- PostgreSQL.
- Docker.
- Alembic.
- Redis, where needed for caching or operational support.

## Roadmap

- Define the core runbook and incident data models.
- Build the initial API surface for reading and managing operational knowledge.
- Add authentication and access control.
- Introduce search, filtering, and metadata enrichment.
- Extend the service with integrations and automation support.

## Status

Early development.
