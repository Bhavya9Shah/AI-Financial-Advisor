\# FinSight — AI Financial Advisor



FinSight is a full-stack AI-powered financial advisory application that combines conversational AI, financial calculation tools, persistent user profiles, and deterministic response evaluation.



The application uses a Gemini-powered LangChain agent to understand financial queries, select appropriate tools, perform calculations, retrieve financial information, and generate grounded responses through an interactive web interface.

## Demo

### Dashboard

![FinSight Dashboard](screenshots/dashboard.png)

### AI Chat

![FinSight AI Chat](screenshots/chat.png)

### Evaluation Framework

![FinSight Evaluation](screenshots/evaluation.png)

### Architecture

![FinSight Architecture](screenshots/architecture.png)

\## Features



\- Conversational AI financial assistant powered by Gemini

\- Tool-based agent architecture using LangChain

\- Persistent financial profile memory

\- Stock information retrieval

\- SIP return and CAGR calculators

\- Financial news retrieval and sentiment analysis

\- Tool execution and reasoning timeline visualization

\- Profile management through the web interface

\- Deterministic response evaluation across multiple quality dimensions

\- Backend health monitoring

\- Automated backend test suite with 61 passing tests

\- Production deployment with continuous deployment workflow



\## Architecture



FinSight follows a full-stack architecture:


## Architecture

```text
┌──────────────────────────────────────────────────────────────────────┐
│                         Next.js Frontend                            │
│                                                                      │
│   Dashboard       AI Chat       Profile       Evaluation             │
│                                                                      │
│                  TypeScript • Tailwind CSS                           │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                                │ REST API
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                              │
│                                                                      │
│        Health API       Chat API       Profile API                   │
│                                                                      │
│                 Request / Response Validation                        │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       LangChain ReAct Agent                          │
│                                                                      │
│                       Gemini 2.5 Flash                               │
│                                │                                     │
│                    Tool Selection & Execution                        │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
              ┌─────────────────┼──────────────────┐
              │                 │                  │
              ▼                 ▼                  ▼
┌───────────────────┐ ┌───────────────────┐ ┌────────────────────────┐
│ Financial Tools   │ │  Profile Memory   │ │   External Data        │
│                   │ │                   │ │                        │
│ • SIP Calculator  │ │ • User Profile    │ │ • Stock Information    │
│ • CAGR Calculator │ │ • Profile Updates │ │ • Financial News       │
│                   │ │ • Completeness    │ │ • News Sentiment       │
└─────────┬─────────┘ └─────────┬─────────┘ └───────────┬────────────┘
          │                     │                       │
          └─────────────────────┼───────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                  Deterministic Evaluation Framework                  │
│                                                                      │
│   Correctness • Grounding • Completeness • Helpfulness • Clarity     │
│                                                                      │
│              Weighted Aggregate Score + Evidence                     │
└──────────────────────────────────────────────────────────────────────┘
```

FinSight uses a layered full-stack architecture. The Next.js client communicates with a FastAPI backend through REST endpoints. Financial queries are processed by a Gemini-powered LangChain ReAct agent, which selects dedicated tools for deterministic calculations, market information, financial news, and profile management.

User financial information is maintained through persistent profile memory and profile-completeness tracking. Responses can be analyzed using a deterministic evaluation framework that measures correctness, grounding, completeness, helpfulness, and clarity without requiring an additional LLM evaluator during inference.