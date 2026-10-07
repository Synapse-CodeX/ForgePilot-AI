# ForgePilot AI

### Autonomous Repository Debugging & Repair Agent

> **From GitHub issue to validated patch — autonomously.**

ForgePilot AI is an autonomous software-engineering agent that investigates issues in Python repositories, identifies root causes, generates code patches, executes tests inside an isolated sandbox, and iteratively repairs failures until the proposed fix is validated.

---

## Overview

Traditional AI coding assistants primarily generate code from prompts.

ForgePilot is designed around a different workflow:

```text
GitHub Repository + Issue
          │
          ▼
   Repository Explorer
          │
          ▼
      Issue Analyst
          │
          ▼
   Code Investigation
          │
          ▼
    Root Cause Analysis
          │
          ▼
     Patch Generation
          │
          ▼
     Docker Sandbox
          │
          ▼
       Test Runner
          │
      ┌───┴───┐
      │       │
    PASS     FAIL
      │       │
      ▼       ▼
 Validation  Self-Correction
      │       │
      └───┬───┘
          ▼
    Validated Patch