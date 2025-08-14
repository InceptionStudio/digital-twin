# Job Update Script

This script allows you to update jobs in the production Firestore database using a JSONL file.

## Overview

The `update_jobs_from_jsonl.py` script:
1. Reads jobs from a JSONL file
2. Finds corresponding jobs in Firestore by matching `video_url`
3. Replaces the entire job document with the data from the file
4. Provides detailed logging and summary statistics

## Usage

### Basic Usage

```bash
# Update jobs from a JSONL file
python update_jobs_from_jsonl.py jobs_to_update.jsonl

# Dry run to see what would be updated (no changes made)
python update_jobs_from_jsonl.py jobs_to_update.jsonl --dry-run

# Specify project ID and collection
python update_jobs_from_jsonl.py jobs_to_update.jsonl --project-id "your-project-id" --collection "jobs"
```

### Environment Variables

The script uses these environment variables:
- `FIRESTORE_PROJECT_ID`: Google Cloud project ID (default)
- `GOOGLE_APPLICATION_CREDENTIALS_JSON`: Base64-encoded service account credentials

## JSONL File Format

Each line in the JSONL file should be a complete JSON object representing a job:

```json
{"id": "job-id", "created_at": "2025-08-14T18:00:00+00:00", "status": "completed", "persona_id": "chad_goldstein", "results": {"video_url": "https://digital-twin-storage.s3.amazonaws.com/videos/job_chad_goldstein_1755074246098.mp4", "hot_take": "Updated hot take text", "output_video": "https://digital-twin-storage.s3.amazonaws.com/videos/job_chad_goldstein_1755074246098.mp4", "file_size": 6881870, "s3_key": "videos/job_chad_goldstein_1755074246098.mp4", "content_type": "video/mp4"}, "updated_at": "2025-08-14T19:00:00+00:00"}
```

### Required Fields

- `results.video_url`: Used to match jobs in Firestore (required)
- All other fields will replace the existing job data

## How It Works

1. **Load Jobs**: Reads each line from the JSONL file as a JSON object
2. **Find Matching Jobs**: Searches Firestore for jobs with matching `video_url`
3. **Update Jobs**: Replaces the entire job document with the new data
4. **Log Results**: Provides detailed logging of successes and failures

## Safety Features

- **Dry Run Mode**: Use `--dry-run` to see what would be updated without making changes
- **Validation**: Checks that jobs exist before attempting updates
- **Error Handling**: Continues processing even if individual jobs fail
- **Detailed Logging**: Shows exactly what happened with each job

## Example Output

```
2025-08-14 19:30:00,123 - INFO - Initializing Firestore storage with project: digital-twin-887dc
2025-08-14 19:30:00,456 - INFO - Loaded 2 jobs from jobs_to_update.jsonl
2025-08-14 19:30:00,789 - INFO - Processing 2 jobs...
2025-08-14 19:30:01,012 - INFO - Processing job 1/2
2025-08-14 19:30:01,345 - INFO - Successfully updated job bf572b5e-0305-4a3c-b20d-d6919f442d29
2025-08-14 19:30:01,678 - INFO - Processing job 2/2
2025-08-14 19:30:02,001 - INFO - Successfully updated job b6e157a7-dc50-40ea-86f9-8fd52f1701d6
2025-08-14 19:30:02,234 - INFO - ============================================================
2025-08-14 19:30:02,234 - INFO - JOB UPDATE SUMMARY
2025-08-14 19:30:02,234 - INFO - ============================================================
2025-08-14 19:30:02,234 - INFO - Total jobs in JSONL file: 2
2025-08-14 19:30:02,234 - INFO - Successful updates: 2
2025-08-14 19:30:02,234 - INFO - Failed updates: 0
2025-08-14 19:30:02,234 - INFO - Skipped updates: 0
2025-08-14 19:30:02,234 - INFO - Job updates completed!
```

## Common Use Cases

1. **Bulk Hot Take Updates**: Update `hot_take` fields for multiple jobs
2. **Data Migration**: Migrate jobs from one format to another
3. **Data Correction**: Fix incorrect data in existing jobs
4. **Status Updates**: Update job statuses in bulk

## Troubleshooting

### "No job found with video_url"
- Verify the `video_url` in your JSONL file matches exactly
- Check that the job exists in Firestore
- Ensure you're connecting to the correct project

### "Job not found in Firestore"
- The job ID might be incorrect
- The job might have been deleted
- Check Firestore permissions

### "Invalid JSON on line X"
- Check the JSON syntax in your JSONL file
- Ensure each line is valid JSON
- Remove any empty lines or malformed data
