# KYC/KYB Onboarding Backend

A backend application for handling KYC (Know Your Customer) and KYB (Know Your Business) onboarding processes.

## Features

- Document upload and storage in S3
- Document data extraction using OCR and ChatGPT
- Integration with third-party data sources via plugins
- Risk assessment using LLM reasoning
- AG Grid compatible API for advanced data tables
- Configurable fraud scoring system

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Storage**: AWS S3
- **AI Processing**: OpenAI GPT-4
- **Document Processing**: Tesseract OCR, pdf2image
- **Container**: Docker & Docker Compose

## Project Structure

```
kyc-kyb-backend/
├── app/                  # Application code
│   ├── api/              # API endpoints
│   ├── core/             # Core utilities
│   ├── db/               # Database configuration
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic services
│   ├── main.py           # FastAPI application 
│   └── config.py         # Configuration
├── alembic/              # Database migrations
├── tests/                # Tests
├── .env                  # Environment variables
├── .env.example          # Example environment variables
├── requirements.txt      # Python dependencies
├── docker-compose.yml    # Docker Compose configuration
└── Dockerfile            # Docker build configuration
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.10 or higher (for local development)
- AWS S3 bucket (or you can use LocalStack for development)
- OpenAI API key
- Sift API key (or other fraud detection service)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/kyc-kyb-backend.git
   cd kyc-kyb-backend
   ```

2. Create .env file:
   ```
   cp .env.example .env
   ```
   Update the environment variables in the .env file with your credentials.

3. Start the application with Docker Compose:
   ```
   docker-compose up -d
   ```

4. Apply database migrations:
   ```
   docker-compose exec api alembic upgrade head
   ```

5. The API will be available at http://localhost:8000

6. API documentation will be available at http://localhost:8000/docs

### Local Development

1. Set up a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   uvicorn app.main:app --reload
   ```

## API Endpoints

### Users
- `POST /api/v1/users/` - Create a new user
- `GET /api/v1/users/{user_id}` - Get user details
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user
- `POST /api/v1/users/list` - List users with AG Grid integration

### Documents
- `POST /api/v1/documents/upload` - Upload a document
- `GET /api/v1/documents/{document_id}` - Get document details
- `GET /api/v1/documents/user/{user_id}` - Get all documents for a user
- `DELETE /api/v1/documents/{document_id}` - Delete a document
- `POST /api/v1/documents/reprocess/{document_id}` - Reprocess a document

### Assessments
- `POST /api/v1/assessments/` - Request a new risk assessment
- `GET /api/v1/assessments/{assessment_id}` - Get assessment details
- `GET /api/v1/assessments/user/{user_id}` - Get all assessments for a user
- `GET /api/v1/assessments/latest/user/{user_id}` - Get the latest assessment for a user
- `DELETE /api/v1/assessments/{assessment_id}` - Delete an assessment

## Adding New Data Source Plugins

To add a new data source plugin:

1. Create a new file in `app/services/plugins/` (e.g., `my_plugin.py`)
2. Implement the `BasePlugin` interface
3. Add the plugin name to the `ENABLED_PLUGINS` setting in `.env`

Example plugin implementation:

```python
from typing import Dict, Any
from app.services.plugins.base_plugin import BasePlugin

class MyPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "my_plugin"
    
    @property
    def description(self) -> str:
        return "My custom data source plugin"
    
    def execute(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implement plugin logic here
        return {"result": "data from my plugin"}
    
    def validate_response(self, response: Dict[str, Any]) -> bool:
        return "result" in response
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

## License

[MIT License](LICENSE)