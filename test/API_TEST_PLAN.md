## What to test
### Endpoints
- **POST `/extract`**
  - Happy path: valid invoice file → returns extracted structured invoice JSON.
  - Validation: missing or invalid file input → returns an error response.
  - Low-confidence or unsupported document type handling → returns 400.
  - FAILURE: OCI service unavailable → returns 503.
  - EDGE CASE: valid document with no extracted fields → returns 200 with empty data.
- **GET `/invoice/{invoice_id}`**
  - Happy path: existing invoice ID → returns the invoice details.
  - Not found: non-existing invoice ID → returns 404 with a clear message.
- **GET `/invoices/vendor/{vendor_name}`**
  - Happy path: vendor with existing invoices → returns vendor details and a list of invoices.
  - Not found: vendor with no invoices → returns empty list with total count = 0.
---
## Test design strategy
- The API is tested using an **integration testing strategy**.
- Tests interact with the API layer using **FastAPI TestClient**, simulating real HTTP requests.
- The database layer is real (SQLite) and initialized before each test.
- Test data is seeded into the database during setup to simulate previous API calls.
- External dependencies (OCI Document AI service) are **mocked** to avoid reliance on external services and credentials.
- This approach validates the integration between:
  - API layer
  - Database layer
  - Business logic  
  while keeping tests deterministic and isolated.
---
## Test environment
- **Local**:
  - Tests are executed in a Python virtual environment using `pytest`.
- **CI (GitHub Actions)**:
  - Tests are executed automatically on Linux runners.
  - No OCI configuration or secrets are available in CI.
  - All external OCI calls are mocked.
  - Application import must not depend on `~/.oci/config`.
---
## Success criteria
- **100% API endpoint coverage**:
  - Every exposed API endpoint has at least:
    - One happy-path test
    - One negative or edge-case test
- **High code coverage**:
  - Aim for as close as possible to **100% coverage** of API code.
- **CI stability**:
  - All tests must pass consistently in GitHub Actions without external dependencies.
---
## Reporting
- **Console output**:
  - Test execution and failures are visible via `pytest -v`.
- **Code coverage**:
  - Coverage is measured using `pytest-cov`.
  - Coverage results are uploaded to **Codecov** and displayed in pull requests.