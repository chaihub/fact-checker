# fact-checker

A Python-based fact-checking tool integrated with WhatsApp for verifying tweets and claims.

## Architecture

[View system diagram](factchecker.drawio)

The FactChecker System processes user queries, leverages a local database and external websites for verification, and returns responses with authenticity verdicts, differences, and references. The recommended architecture consists of:

- **Frontend/Chat Interface**: A WhatsApp bot (using Twilio or similar API) to receive user messages and send responses. Include input parsing for text, images (e.g., OCR for screenshots), and queries.

- **API Layer**: Use FastAPI (Python) for REST endpoints handling requests from the chat interface. Handle authentication, rate limiting, and message routing.

- **Fact-Checking Engine**: Core logic module (Python classes/functions) for:
  - Text analysis (NLP with libraries like spaCy or NLTK for claim extraction).
  - Verification against local DB (e.g., SQLite with pre-stored facts) and external sources (web scraping with BeautifulSoup or APIs like Twitter's).
  - Output generation: Authenticity scores, differences, yes/no answers, with citations.

- **Data Layer**: 
  - Local DB for cached facts and user history.
  - External integrations: API calls to fact-check sites (e.g., Snopes, FactCheck.org) or Twitter API for tweet verification.

- **Supporting Services**: Logging (e.g., with Python's logging module), error handling, and async processing (asyncio) for external calls.

- **Deployment**: Containerize with Docker, deploy on cloud (e.g., AWS Lambda for serverless API).
