# Database Utilities

This directory contains utilities for backing up and restoring the Firestore database.

## Utilities

### 1. `dump_firestore_database.py` - Database Backup Utility

Dumps the entire Firestore database to JSON format for easy backup, migration, or analysis.

#### Features:
- ✅ **Complete Database Dump** - Exports all documents from Firestore collections
- ✅ **Filtering Options** - Filter by status, limit number of documents
- ✅ **Summary Generation** - Creates database statistics and breakdowns
- ✅ **Timestamp Handling** - Converts datetime objects to ISO format strings
- ✅ **Documentation** - Auto-generates README files with dump information
- ✅ **Flexible Output** - Pretty-printed or compact JSON, custom output directories

#### Usage:

```bash
# Basic dump of entire database
python dump_firestore_database.py

# Dump with filtering
python dump_firestore_database.py --status completed --limit 100

# Summary only (no data dump)
python dump_firestore_database.py --summary-only

# Custom output directory
python dump_firestore_database.py --output-dir ./my_backup

# Compact JSON (no pretty printing)
python dump_firestore_database.py --no-pretty
```

#### Output Files:
- `firestore_dump_YYYYMMDD_HHMMSS.json` - Main data dump
- `database_summary.json` - Database statistics and breakdowns
- `README.md` - Documentation with import instructions

#### Example Output:
```json
{
  "dump_timestamp": "2025-08-14T20:49:17.459877+00:00",
  "database_info": {
    "project_id": "digital-twin-887dc",
    "collection": "jobs"
  },
  "statistics": {
    "total_jobs": 46,
    "status_breakdown": {
      "completed": 46
    },
    "persona_breakdown": {
      "Russ Hanneman": 8,
      "Chad Goldstein": 14,
      "Sarah Guo": 22,
      "unknown": 2
    },
    "step_breakdown": {
      "video_generation": 44,
      "text_processing": 2
    }
  }
}
```

---

### 2. `import_firestore_database.py` - Database Restore Utility

Imports data from JSON files back into Firestore, with conflict resolution options.

#### Features:
- ✅ **Safe Import** - Dry-run mode to preview changes
- ✅ **Conflict Resolution** - Skip, overwrite, or error on conflicts
- ✅ **Validation** - Validates JSON format and document structure
- ✅ **Progress Tracking** - Shows import progress and statistics
- ✅ **Error Handling** - Graceful handling of import errors

#### Usage:

```bash
# Validate JSON file only
python import_firestore_database.py dump_file.json --validate-only

# Dry run (preview what would be imported)
python import_firestore_database.py dump_file.json --dry-run

# Import with conflict handling
python import_firestore_database.py dump_file.json --conflict skip
python import_firestore_database.py dump_file.json --conflict overwrite
python import_firestore_database.py dump_file.json --conflict error

# Import to different collection
python import_firestore_database.py dump_file.json --collection backup_jobs
```

#### Conflict Resolution Options:
- `skip` (default) - Skip documents that already exist
- `overwrite` - Replace existing documents with imported data
- `error` - Stop import if any conflicts are found

#### Example Output:
```
============================================================
IMPORT SUMMARY
============================================================
Total documents: 46
Imported: 0
Skipped: 46
Overwritten: 0
Errors: 0
Import completed!
```

---

## Environment Setup

Both utilities require the following environment variables:

```bash
export JOB_STORAGE=firestore
export FIRESTORE_PROJECT_ID=your-project-id
export FIRESTORE_COLLECTION=jobs  # optional, defaults to "jobs"
```

Or create a `.env` file:
```env
JOB_STORAGE=firestore
FIRESTORE_PROJECT_ID=your-project-id
FIRESTORE_COLLECTION=jobs
```

## Use Cases

### 1. **Database Backup**
```bash
# Create a complete backup
python dump_firestore_database.py --output-dir ./backups/$(date +%Y%m%d)
```

### 2. **Data Migration**
```bash
# Dump from source
python dump_firestore_database.py --output-dir ./migration

# Import to target (with overwrite)
python import_firestore_database.py ./migration/firestore_dump_*.json --conflict overwrite
```

### 3. **Data Analysis**
```bash
# Get summary only for analysis
python dump_firestore_database.py --summary-only

# Dump specific data for analysis
python dump_firestore_database.py --status completed --limit 1000
```

### 4. **Development/Testing**
```bash
# Create test data dump
python dump_firestore_database.py --limit 10 --output-dir ./test_data

# Import test data to development environment
python import_firestore_database.py ./test_data/firestore_dump_*.json --dry-run
```

## File Formats

### JSON Structure
The dump creates JSON files with the following structure:
```json
[
  {
    "id": "document-id",
    "status": "completed",
    "persona_id": "russ_hanneman",
    "persona_name": "Russ Hanneman",
    "created_at": "2025-08-13T08:19:06+00:00",
    "updated_at": "2025-08-14T20:05:59.689878+00:00",
    "step": "video_generation",
    "results": {
      "video_url": "https://...",
      "hot_take": "..."
    }
  }
]
```

### Timestamp Format
All timestamps are stored as ISO format strings with timezone:
- Format: `"YYYY-MM-DDTHH:MM:SS+00:00"`
- Example: `"2025-08-13T08:19:06+00:00"`

## Safety Features

### Dump Safety
- ✅ **Read-only operations** - Dump never modifies the database
- ✅ **Error handling** - Continues processing even if individual documents fail
- ✅ **Progress tracking** - Shows progress for large dumps

### Import Safety
- ✅ **Dry-run mode** - Preview changes before applying
- ✅ **Validation** - Validates JSON structure before import
- ✅ **Conflict resolution** - Configurable handling of existing documents
- ✅ **Error recovery** - Continues processing on individual document errors

## Troubleshooting

### Common Issues

1. **Firestore Index Errors**
   ```
   The query requires an index
   ```
   - **Solution**: The dump utility automatically skips ordering when filtering to avoid index requirements

2. **Permission Errors**
   ```
   Permission denied
   ```
   - **Solution**: Ensure Google Cloud credentials are properly configured

3. **Large File Handling**
   - For very large databases, consider using limits or filters
   - Monitor memory usage during import operations

### Performance Tips

1. **Large Databases**: Use `--limit` to process in chunks
2. **Network Issues**: Use `--no-pretty` for smaller file sizes
3. **Memory Usage**: Process large files in smaller batches

## Integration with Other Tools

### Update Jobs Script
The dumped JSON files can be used with `update_jobs_from_jsonl.py`:
```bash
# Convert JSON to JSONL format
jq -c '.[]' dump_file.json > jobs.jsonl

# Update jobs using the existing script
python update_jobs_from_jsonl.py jobs.jsonl
```

### Version Control
- Dump files can be version controlled for tracking database changes
- Use `--output-dir` with timestamps for historical tracking
- Consider excluding large dump files from git with `.gitignore`

## Security Considerations

1. **Credentials**: Never commit Google Cloud credentials to version control
2. **Data Sensitivity**: Be careful with dump files containing sensitive data
3. **Access Control**: Limit access to dump files in production environments
4. **Backup Storage**: Store backups in secure, encrypted locations
