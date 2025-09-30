> [!WARNING]
> :construction: This repo & project are getting revamped in Fall 2025 - this was created as a Proof of Concept, and the service is not currently running or confirmed to be working as-is.  More to come.

# Georgia CourtBot

Helping people remember to attend court to help break the cycle of fines and jail time.

## About

Georgia CourtBot is a civic tech project that sends SMS reminders to people with upcoming court hearings in DeKalb County, Georgia. By providing timely reminders, we help reduce missed court dates and the resulting consequences like additional fines, warrants, and jail time.

## Current Status: Version 2 (mostly built)

✅ **Implemented:**
- DeKalb County hearing data scraper (automated daily cloud runs)
- BigQuery data storage and management
- SMS reminder system via Twilio
- Case number lookup and validation
- Scheduled hearing notifications

🚧 **In Progress:**
- Public-facing website for self-service sign-up
- Additional counties and municipalities

## Architecture

This system consists of three primary components:

### 1. Python Scraper (`scraper/`)
Scrapes DeKalb County court system for hearing data:
- Searches by judicial officer to handle API pagination limits
- Validates data against JSON schema
- Outputs CSV/JSON format
- Handles ~200 record API limit with recursive pagination

### 2. Cloud Run Service (`cloudrun/main.py`)
Automated daily scraper execution:
- Containerized Flask application on Google Cloud Run
- Triggered by GitHub Actions or HTTP requests
- Uploads scraped data to BigQuery
- Appends new records to existing dataset

### 3. SMS Notification System
Two serverless functions for SMS functionality:

**Twilio Functions** (`twilio/twilio_functions.js`):
- Validates case numbers from user input
- Queries BigQuery for hearing details
- Returns date, time, and courtroom information

**Google Cloud Function** (`google/hearingNotificationSend/`):
- Queries hearings from BigQuery view `HEARING_NOTIFY_VIEW`
- Sends SMS reminders via Twilio
- **Note**: Date filtering logic and Cloud Scheduler setup not in this repository

## Quick Start

### Prerequisites
- Python 3.10+
- Google Cloud Platform account with BigQuery enabled
- Twilio account for SMS functionality

### Local Development

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Run scraper locally:**
```bash
# Output to CSV
python -m scraper scrape --output csv --days 90

# Output to JSON
python -m scraper scrape --output json --days 30
```

**Upload data to BigQuery:**
```bash
python -m scraper upload \
  --key-path /path/to/gcp-key.json \
  --table-id 'project.dataset.table' \
  --data data.csv
```

### Docker Deployment

**Build image:**
```bash
docker build -t georgia-courtbot .
```

**Run locally:**
```bash
docker run \
  -e PROJECT_ID=your-project \
  -e DATASET_ID=your-dataset \
  -e TABLE_ID=your-table \
  -p 8080:8080 \
  georgia-courtbot
```

## Data Schema

Court hearing records contain the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `CaseId` | INTEGER | Unique case identifier |
| `CaseNumber` | STRING | Court case number (e.g., 22CR12345) |
| `JudicialOfficer` | STRING | Assigned judge name |
| `HearingDate` | STRING | Date in MM/DD/YYYY format |
| `HearingTime` | STRING | Hearing time |
| `CourtRoom` | STRING | Courtroom location |

### Case Number Formats

The system recognizes these case number patterns:
- `(\d{2})([A-Z]{1,2})(\d{4,5})` - Example: 22CR12345
- `([A-Z]{1})(\d{7})` - Example: C1234567

## Configuration

### Environment Variables

**Cloud Run Service:**
- `PROJECT_ID` - Google Cloud project ID
- `DATASET_ID` - BigQuery dataset name
- `TABLE_ID` - BigQuery table name
- `PORT` - HTTP port (default: 8080)

**Twilio/Google Cloud Functions:**
- `TWILIO_ACCOUNT_SID` - Twilio account identifier
- `TWILIO_AUTH_TOKEN` - Twilio authentication token
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to GCP service account JSON

## Known Issues & Limitations

- **SSL Certificate Workaround**: DeKalb County server returns incomplete certificate chain, requiring SSL verification to be disabled in the scraper
- **Single County**: Currently only supports DeKalb County
- **API Pagination**: DeKalb County API limits results to ~200 records per query (handled by searching per judicial officer)
- **No Incremental Updates**: Scraper re-scrapes entire date range rather than detecting changes

See [GitHub Issues](https://github.com/CivicTechAtlanta/georgia-courtbot/issues) for complete list.

## Roadmap

### Version 3+ (Future)
- Additional metro Atlanta counties (Fulton, Cobb, Gwinnett, etc.)
- Public-facing website for self-service sign-up
- PII security enhancements (phone number anonymization)
- Scraper v2: On-demand scraping for subscribed cases only
- Integration with other courtbot implementations
- Additional messaging channels beyond SMS
- Enhanced chatbot features

## Contributing

We welcome contributions! Here's how to get involved:

1. Join the [Civic Tech Atlanta Slack](https://civictechatlanta.slack.com) → `#georgia-courtbot` channel
2. Review open [issues](https://github.com/CivicTechAtlanta/georgia-courtbot/issues)
3. Check the [Quick Start Guide](https://docs.google.com/document/d/1folvVL2UYl3UeBU9jRcmf5AXU74px8gJmmkvKt6KJ7Q/edit?usp=sharing)
4. Pick an issue labeled `good first issue` to get started

### Areas Where We Need Help

**Backend Development:**
- Python web scraping and API development
- Google Cloud Platform (Cloud Run, BigQuery)
- Database design and optimization

**Frontend Development:**
- Public-facing website (similar to https://court.bot)
- User sign-up flows and forms

**Research:**
- Identifying other Georgia counties with online court data
- Existing court notification systems in Georgia
- User research and usability testing

**Design:**
- UX flows for SMS conversations
- Website design and user experience
- Form design for sign-up process

## Technical Details

For detailed technical documentation including architecture and data flow, see [ARCHITECTURE.md](ARCHITECTURE.md)

## License

This project is maintained by [Civic Tech Atlanta](https://www.civicTechatlanta.org/)

## Contact

- Slack: [#georgia-courtbot channel](https://civicTechatlanta.slack.com)
- Issues: [GitHub Issues](https://github.com/CivicTechAtlanta/georgia-courtbot/issues)
- Civic Tech Atlanta: https://www.civicTechatlanta.org/
