# django-dynamo demo

A Django REST API backed by DynamoDB via PynamoDB. Models: `Product` and `OrderEvent` (append-only event log).

## Setup

```bash
pip install -r requirements.txt
python manage.py migrate   # SQLite for Django internals only
```

Set env vars (or use `.env`):
```
AWS_DEFAULT_REGION=us-east-1
DYNAMODB_HOST=http://localhost:8000   # local DynamoDB
```

## Structure

- `store/models.py` — PynamoDB table definitions (`ProductTable`, `OrderEventTable`)
- `store/dynamo.py` — Read/write helpers with query patterns
- `store/views.py` — DRF ViewSets
- `store/urls.py` — URL routing
- `store/tests/` — pytest tests using moto
