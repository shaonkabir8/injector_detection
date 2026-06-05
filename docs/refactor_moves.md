# Refactor Moves

## Goal
Turn the current Brick Kiln detector into a reusable, standalone AI Detection Engine with a clear plug-and-play architecture.

## Architecture Diagram

```text
                           ┌──────────────────────────┐
                           │   External System       │
                           │  Laravel / Node / ERP   │
                           │  Warehouse / Fleet      │
                           └──────────┬──────────────┘
                                      │
                                      ▼
                           ┌──────────────────────────┐
                           │    SecurityOS API        │
                           │  FastAPI / Auth / Input  │
                           │  Validation / Routing    │
                           └──────────┬──────────────┘
                                      │
                                      ▼
                           ┌──────────────────────────┐
                           │      Orchestration       │
                           │  Request Router / Queue  │
                           │  Source Node Manager     │
                           └──────────┬──────────────┘
                                      │
                ┌─────────────────────┼─────────────────────┐
                │                     │                     │
                ▼                     ▼                     ▼
       ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
       │ Motion Worker    │   │ Detection Worker │   │ OCR Worker      │
       │ (motion trigger) │   │ (YOLO / fusion)  │   │ (plate search + │
       │                 │   │                 │   │  OCR pipeline)  │
       └──────┬──────────┘   └──────┬──────────┘   └──────┬──────────┘
              │                     │                     │
              │                     │                     │
              ▼                     ▼                     ▼
       ┌─────────────────────────────────────────────────────┐
       │                 Per-Vehicle Pipeline                │
       │                                                     │
       │  ┌──────────┐  ┌───────────────┐  ┌───────────────┐ │
       │  │SubType    │  │ Load Classifier│  │Material Class. │ │
       │  │Classifier │  │ (cargo mask)   │  │ (cargo mask)   │ │
       │  └────┬─────┘  └─────┬─────────┘  └─────┬─────────┘ │
       │       │              │                │           │
       │       ▼              ▼                ▼           │
       │  ┌───────────────────────────────────────────────┐ │
       │  │             Fusion + Confidence             │ │
       │  │   score combination, fallback model trigger  │ │
       │  └───────────────────────────────────────────────┘ │
       └─────────────────────────────────────────────────────┘
                                      │
                                      ▼
                           ┌──────────────────────────┐
                           │   Validation Layer       │
                           │ External ERP / Registry  │
                           │ API Validation / Gate    │
                           └──────────┬──────────────┘
                                      │
                                      ▼
                           ┌──────────────────────────┐
                           │   Audit & Learning       │
                           │  event log / dataset     │
                           │  correction / retrain    │
                           └──────────┬──────────────┘
                                      │
                                      ▼
                           ┌──────────────────────────┐
                           │   Result Response        │
                           │  FullDetectionResponse   │
                           │  vehicles[], load,       │
                           │  material, plate, gate   │
                           └──────────────────────────┘
```

## Refactor Moves

1. Separate API layer from engine layer
   - Keep `main.py`/FastAPI as API facade only.
   - Create `DetectionEngine` service that is reusable and pluggable.

2. Make source nodes isolated
   - Add `SourceNode` concept per camera/source.
   - Use workers for motion, detection, OCR, validation.

3. Keep business logic external
   - Use external validation API instead of embedded approval rules.
   - Only emit validation requests and consume responses.

4. Use a queue/event layer
   - Define core events: `camera.motion`, `camera.detect`, `camera.ocr`, `camera.validate`, `camera.audit`, `camera.learn`.
   - Abstract queue backend so Redis/Rabbit/Kafka can be swapped.

5. Standardize per-vehicle result model
   - Keep `VehicleResult` and `FullDetectionResponse` as source contract.
   - Ensure all models write into per-vehicle output, not global state.

6. Implement confidence fusion
   - Add secondary detector/fallback trigger for low confidence.
   - Combine detection, OCR, material, load scores.

7. Build audit/learning pipeline
   - Store `input`, `prediction`, `validation`, `final_outcome`.
   - Create dataset records for future retraining.

8. Harden security and integration
   - Require token auth, rate limit, input validation.
   - Keep engine API stateless and secure.

## Why this diagram

This design turns the current project into a true standalone Detection Engine with:

- API-first integration layer
- isolated source/workers
- modular per-vehicle pipeline
- external validation
- audit/learning feedback

It aligns with `docs/BLUEPRINT.md` while keeping the existing model flow and FastAPI service.
