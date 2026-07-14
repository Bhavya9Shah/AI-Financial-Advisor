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



```text

Next.js Frontend

&#x20;       |

&#x20;       | REST API

&#x20;       v

FastAPI Backend

&#x20;       |

&#x20;       v

LangChain ReAct Agent

&#x20;       |

&#x20;       +---- Gemini 2.5 Flash

&#x20;       |

&#x20;       +---- Financial Tools

&#x20;       |       |

&#x20;       |       +---- Stock Information

&#x20;       |       +---- SIP Calculator

&#x20;       |       +---- CAGR Calculator

&#x20;       |       +---- Financial News

&#x20;       |       +---- Profile Management

&#x20;       |

&#x20;       +---- Persistent Profile Memory

&#x20;       |

&#x20;       +---- Deterministic Evaluation Framework

