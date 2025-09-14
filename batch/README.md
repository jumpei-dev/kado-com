# Batch Processing Module

このモジュールは `/Users/admin/Projects/kado-com/README.md` に統合されました。

メインREADMEを参照してください：
- プロジェクト全体の構成
- 最新実装機能（capacity補正、受付終了判定等）
- 詳細なコマンドライン操作
- DOM確認モード
- テスト機能

## クイックリファレンス

```bash
# メインディレクトリから実行
cd /Users/admin/Projects/kado-com

# 基本操作
python batch/main.py test-db
python batch/main.py collect --force
python batch/main.py calculate --date 2025-09-05

# 新機能テスト
python batch/main.py test-working-rate --business-id 1 --date 2025-09-05 --capacity 6 --type soapland
python batch/main.py debug-html --url "https://example.com/attend/"
```
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
export STATUS_COLLECTION_INTERVAL="120"  # minutes (GitHub Actionsと統一: 2時間間隔)
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
