# CLAUDE.md

## Purpose

Standalone AI Detection Service for external systems.
Designed as independent plug-and-play detection layer, not business logic owner.

## Vision

Detect. Verify. Learn. Audit. Report. Respond.
Connect via REST API, GraphQL, Webhooks, MQTT, Kafka, WebSocket, SDKs.

## Core Features

- Motion detection
- Vehicle detection
- Material detection
- Load detection
- OCR / plate/container/license scanning
- Evidence builder
- Validation engine
- Audit engine
- Learning pipeline

## Architecture

External System -> SecurityOS API -> AI Detection Engine

Each source is isolated as a node:
- Stream worker
- Motion worker
- Detection worker
- OCR worker
- Validation worker
- Learning worker
- Audit worker
- Health worker

## Isolation Rules

If one source fails:
- restart worker
- restart pipeline
- reconnect stream
Never restart whole system.

## Supported Inputs

- RTSP, ONVIF, IP camera, USB camera
- DVR, NVR, HTTP/SRT/WebRTC streams
- Video files, uploads, mobile/drone feeds

## Detection Modules

### Vehicle
- truck, pickup, van, bus, bike, tractor, heavy vehicle, custom classes

### Material
- brick, sand, soil, clay, stone
- custom materials without core retrain

### Load
- empty, partial, full, overloaded

### OCR
- license plate, container number, gatepass, invoice, QR, barcode
- capture confidence, timestamp, source, frame, evidence

### Verification
- face recognition
- driver matching

## Principles

- Security first
- Simple over complex
- Production ready, not demo ready
- Automation everywhere
- Self-healing
- Observability
- Least privilege

## Requirements

- JWT/token auth
- Rate limiting
- Validation + sanitization
- Audit logging
- Secure headers
- Role-based permissions
- Real-time alerts + error tracking

## Preferred Stack

- Backend: Laravel, PHP, Node.js
- Frontend: React, Next.js, TypeScript, Tailwind
- Data: PostgreSQL, MySQL, Redis
- Infra: Docker, Nginx, Ubuntu, GitHub Actions
- AI: OpenAI, Claude, Gemini, local LLMs, Ollama

## Documentation

Every feature must include overview, architecture, install, config, deploy, troubleshoot.

## Mission

Build enterprise-grade, secure, scalable detection service that integrates with any external platform.
