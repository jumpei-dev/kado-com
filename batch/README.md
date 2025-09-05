# 稼働.com Batch Processing System

This batch processing system automatically collects and analyzes cast working status for the wind industry activity tracking platform.

## Features

- **Status Collection**: Automatically scrape cast working status every 30 minutes during business hours
- **History Calculation**: Calculate daily working rates every 6 hours for historical analysis
- **Multi-site Support**: Supports CityHeaven and DTO (デリヘルタウン) scraping
- **Robust Scheduling**: APScheduler-based job scheduling with proper error handling
- **Comprehensive Logging**: Structured logging with rotation and different log levels
- **Database Integration**: Direct PostgreSQL connection to Supabase

## Architecture

```
batch/
├── core/              # Core business logic
│   ├── database.py    # Database operations
│   ├── models.py      # Data models
│   └── scraper.py     # Web scraping logic
├── jobs/              # Batch jobs
│   ├── status_collection.py  # Status collection job
│   └── working_rate_calculation.py # Working rate and history calculation job
├── scheduler/         # Job scheduling
│   └── main.py        # Main scheduler daemon
├── utils/             # Utilities
│   ├── config.py      # Configuration management
│   ├── datetime_utils.py  # Date/time utilities
│   └── logging_utils.py   # Logging utilities
└── main.py            # CLI entry point
```

## Installation

1. Install dependencies:
```bash
cd batch
pip install -r requirements.txt
```

2. Verify database connection:
```bash
python main.py test-db
```

## Usage

### Run the Scheduler Daemon
```bash
python main.py scheduler
```
This runs the scheduler daemon that automatically executes jobs based on business hours and intervals.

### Manual Job Execution

#### Status Collection
```bash
# Collect status for all businesses (respects business hours)
python main.py collect

# Force collection outside business hours
python main.py collect --force

# Collect for specific business only
python main.py collect --business-id 1
```

#### History Calculation
```bash
# Calculate history for all businesses (respects timing)
python main.py history

# Force calculation at any time
python main.py history --force

# Calculate for specific date
python main.py history --date 2024-01-15

# Calculate for specific business
python main.py history --business-id 1
```

#### Get Summary Reports
```bash
# Get 7-day summary for business
python main.py summary --business-id 1

# Get 30-day summary
python main.py summary --business-id 1 --days 30
```

## Configuration

Configuration can be provided via:
1. Environment variables (default)
2. JSON configuration file

### Environment Variables
```bash
export DATABASE_URL="postgresql://user:pass@host:port/db"
export LOG_LEVEL="INFO"
export STATUS_COLLECTION_INTERVAL="30"  # minutes
export HISTORY_CALCULATION_INTERVAL="360"  # minutes
```

### Configuration File
```bash
python main.py --config config.json scheduler
```

## Job Scheduling

### Status Collection
- **Frequency**: Every 30 minutes (configurable)
- **Business Hours**: Only runs during business hours + buffer
- **Buffer**: 30 minutes before/after business hours
- **Purpose**: Collect real-time cast working status

### Status History Calculation
- **Frequency**: Every 6 hours (configurable)  
- **Timing**: After business hours + buffer
- **Buffer**: 60 minutes after business hours end
- **Purpose**: Calculate daily working rate statistics

## Database Schema

The system works with these main tables:
- `business`: Business information and operating hours
- `cast`: Cast profiles and business relationships
- `status`: Real-time working status records
- `status_history`: Daily aggregated working rate statistics

## Logging

Logs are written to:
- `logs/batch_processing.log`: All system logs
- `logs/batch_errors.log`: Error-level logs only
- `logs/jobs_YYYYMMDD.log`: Daily job execution logs

Log rotation is automatic (10MB files, 5 backups).

## Error Handling

- Database connection failures are retried
- Web scraping timeouts are handled gracefully
- Jobs continue processing other items if individual items fail
- Comprehensive error logging and reporting

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black batch/
flake8 batch/
```

## Production Deployment

1. Set environment to production:
```bash
export BATCH_ENVIRONMENT="production"
```

2. Use systemd service or process manager:
```bash
python main.py scheduler
```

3. Monitor logs:
```bash
tail -f logs/batch_processing.log
```

## Troubleshooting

### Database Connection Issues
```bash
python main.py test-db
```

### Check Scheduler Status
Look for "Scheduler running with X jobs" in logs.

### Manual Job Testing
Use `--force` flag to test jobs outside normal scheduling.

## Support

For issues or questions, check the logs first:
- Database errors: Check connection string and Supabase status
- Scraping errors: Check target website availability  
- Scheduling errors: Check business hours configuration
