# GitHub Actions Optimization Guide for Chaptrix

This guide provides recommendations for optimizing the GitHub Actions workflow for Chaptrix to ensure efficient automation, reduce execution time, and minimize resource usage.

## Current Workflow Analysis

The current unified workflow (`unified-workflow.yml`) runs every 4 hours and performs the following steps:

1. Checkout code
2. Set up Python
3. Install dependencies
4. Configure environment variables
5. Set up Google Drive credentials
6. Run the unified workflow
7. Commit changes to comics.json

While this workflow is functional, there are several optimizations that can improve its efficiency and reliability.

## Optimization Recommendations

### 1. Dependency Caching

**Current Issue**: Dependencies are reinstalled on every workflow run, which is time-consuming.

**Solution**: Implement dependency caching to speed up workflow execution.

```yaml
- name: Set up Python
  uses: actions/setup-python@v3
  with:
    python-version: '3.9'
    cache: 'pip'

- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
```

For more complex caching needs:

```yaml
- name: Cache pip dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

### 2. Conditional Execution

**Current Issue**: The workflow runs even when there might be no updates to check.

**Solution**: Add conditional execution based on time or other factors.

```yaml
- name: Check if execution is needed
  id: check_execution
  run: |
    # Example: Only run full workflow during certain hours
    HOUR=$(date +%H)
    if [ $HOUR -ge 8 ] && [ $HOUR -le 23 ]; then
      echo "::set-output name=should_run::true"
    else
      echo "::set-output name=should_run::false"
    fi

- name: Run unified workflow
  if: steps.check_execution.outputs.should_run == 'true'
  run: python unified_workflow.py
```

### 3. Workflow Timeout Management

**Current Issue**: No timeout limits could lead to stuck workflows.

**Solution**: Add timeout limits to prevent workflows from running indefinitely.

```yaml
jobs:
  process:
    runs-on: ubuntu-latest
    timeout-minutes: 30  # Set appropriate timeout
```

### 4. Error Handling and Notifications

**Current Issue**: Limited error handling and notification.

**Solution**: Add better error handling and notifications for workflow failures.

```yaml
- name: Run unified workflow
  id: run_workflow
  run: python unified_workflow.py
  continue-on-error: true

- name: Check workflow result
  if: steps.run_workflow.outcome == 'failure'
  run: |
    echo "Workflow failed, sending notification"
    curl -X POST -H "Content-Type: application/json" \
      -d '{"content":"⚠️ Chaptrix workflow failed! Please check the logs: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"}' \
      ${{ secrets.DISCORD_WEBHOOK_URL }}
```

### 5. Artifact Management

**Current Issue**: No artifacts are saved from workflow runs for debugging.

**Solution**: Save logs and other artifacts for debugging.

```yaml
- name: Run unified workflow
  run: python unified_workflow.py 2>&1 | tee workflow.log

- name: Upload logs
  uses: actions/upload-artifact@v3
  if: always()
  with:
    name: workflow-logs
    path: |
      workflow.log
      *.log
    retention-days: 5
```

### 6. Optimized Checkout

**Current Issue**: Full repository history is checked out.

**Solution**: Use shallow clone to speed up checkout.

```yaml
- uses: actions/checkout@v3
  with:
    fetch-depth: 1  # Shallow clone with only the latest commit
```

### 7. Matrix Strategy for Multiple Sites

**Current Issue**: All sites are processed sequentially.

**Solution**: Use matrix strategy to process multiple sites in parallel.

```yaml
jobs:
  prepare:
    runs-on: ubuntu-latest
    outputs:
      sites: ${{ steps.get-sites.outputs.sites }}
    steps:
      - uses: actions/checkout@v3
      - id: get-sites
        run: echo "::set-output name=sites::$(python -c "import json; print(json.dumps([site for site in json.load(open('comics.json'))['sites']]))")"

  process:
    needs: prepare
    runs-on: ubuntu-latest
    strategy:
      matrix:
        site: ${{ fromJson(needs.prepare.outputs.sites) }}
      fail-fast: false  # Continue with other sites if one fails
    steps:
      - uses: actions/checkout@v3
      # Setup steps...
      - name: Process site
        run: python unified_workflow.py --site ${{ matrix.site }}
```

### 8. Resource Optimization

**Current Issue**: Default GitHub Actions runner might have more resources than needed.

**Solution**: Specify appropriate resource limits.

```yaml
jobs:
  process:
    runs-on: ubuntu-latest
    # GitHub-hosted runners have fixed resources, but you can optimize your code
    # to use resources efficiently
    steps:
      - name: Run with resource optimization
        run: |
          # Set environment variables to limit resource usage
          export PYTHONUNBUFFERED=1
          export PYTHONHASHSEED=0
          # Run with optimized flags
          python -O unified_workflow.py
```

### 9. Scheduled Workflow Optimization

**Current Issue**: Fixed schedule might not be optimal for all users.

**Solution**: Make schedule configurable and optimize frequency.

```yaml
on:
  schedule:
    # Run at different times to distribute load
    - cron: '0 */4 * * *'  # Every 4 hours
  workflow_dispatch:
    inputs:
      full_scan:
        description: 'Run a full scan of all comics'
        required: false
        default: 'false'
      specific_comic:
        description: 'Process a specific comic (leave empty for all)'
        required: false
```

### 10. Workflow Concurrency Control

**Current Issue**: Multiple workflow runs might overlap.

**Solution**: Add concurrency control to cancel outdated runs.

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true  # Cancel in-progress runs when a new workflow is triggered
```

## Complete Optimized Workflow

Here's a complete optimized workflow incorporating all the recommendations:

```yaml
name: Chaptrix Unified Workflow

on:
  schedule:
    - cron: '0 */4 * * *'  # Run every 4 hours
  workflow_dispatch:
    inputs:
      full_scan:
        description: 'Run a full scan of all comics'
        required: false
        default: 'false'
      specific_comic:
        description: 'Process a specific comic (leave empty for all)'
        required: false

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  process:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 1
      
      - name: Set up Python
        uses: actions/setup-python@v3
        with:
          python-version: '3.9'
          cache: 'pip'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          
      - name: Set up environment
        env:
          DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
          DISCORD_BOT_TOKEN: ${{ secrets.DISCORD_BOT_TOKEN }}
          DISCORD_CHANNEL_ID: ${{ secrets.DISCORD_CHANNEL_ID }}
        run: |
          echo "DISCORD_WEBHOOK_URL=$DISCORD_WEBHOOK_URL" > .env
          echo "DISCORD_BOT_TOKEN=$DISCORD_BOT_TOKEN" >> .env
          echo "DISCORD_CHANNEL_ID=$DISCORD_CHANNEL_ID" >> .env
      
      - name: Set up Google Drive credentials
        run: |
          echo '${{ secrets.GOOGLE_CREDENTIALS }}' > credentials.json
          
      - name: Run unified workflow
        id: run_workflow
        run: |
          export PYTHONUNBUFFERED=1
          python unified_workflow.py ${{ github.event.inputs.specific_comic != '' && format('--comic "{0}"', github.event.inputs.specific_comic) || '' }} ${{ github.event.inputs.full_scan == 'true' && '--full-scan' || '' }} 2>&1 | tee workflow.log
        continue-on-error: true
        
      - name: Upload logs
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: workflow-logs
          path: |
            workflow.log
            *.log
          retention-days: 5
          
      - name: Check workflow result
        if: steps.run_workflow.outcome == 'failure'
        run: |
          echo "Workflow failed, sending notification"
          curl -X POST -H "Content-Type: application/json" \
            -d '{"content":"⚠️ Chaptrix workflow failed! Please check the logs: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"}' \
            ${{ secrets.DISCORD_WEBHOOK_URL }}
        
      - name: Commit changes
        if: steps.run_workflow.outcome == 'success'
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add comics.json
          git commit -m "Update comics data [skip ci]" || echo "No changes to commit"
          git push
```

## Additional Optimization Strategies

### 1. Split Workflow into Multiple Jobs

For more complex scenarios, split the workflow into multiple jobs:

```yaml
jobs:
  prepare:
    # Job to prepare environment and determine what to process
    # ...
    
  process:
    needs: prepare
    # Job to process comics
    # ...
    
  notify:
    needs: process
    if: always()
    # Job to send notifications
    # ...
```

### 2. Use GitHub Actions Environment Variables

Leverage GitHub Actions environment variables for better debugging:

```yaml
- name: Run with environment info
  run: |
    echo "Running on: ${{ runner.os }}"
    echo "Repository: ${{ github.repository }}"
    echo "Workflow: ${{ github.workflow }}"
    echo "Run ID: ${{ github.run_id }}"
    python unified_workflow.py
```

### 3. Implement Retry Logic

Add retry logic for network operations:

```yaml
- name: Run with retries
  uses: nick-invision/retry@v2
  with:
    timeout_minutes: 10
    max_attempts: 3
    retry_on: error
    command: python unified_workflow.py
```

## Monitoring and Maintenance

### 1. Regular Workflow Auditing

Regularly review workflow runs to identify:

- Execution time trends
- Common failure points
- Resource usage patterns

### 2. Workflow Analytics

Implement basic analytics to track workflow performance:

```yaml
- name: Record workflow metrics
  run: |
    START_TIME=$(date +%s)
    python unified_workflow.py
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    echo "Workflow duration: $DURATION seconds"
    # Optionally send metrics to a monitoring service
```

### 3. Scheduled Maintenance

Implement a separate maintenance workflow that runs less frequently:

```yaml
name: Chaptrix Maintenance

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday at midnight

jobs:
  maintenance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      # Setup steps...
      - name: Run maintenance tasks
        run: python maintenance.py
```

## Conclusion

By implementing these optimizations, you can significantly improve the efficiency, reliability, and maintainability of your Chaptrix GitHub Actions workflow. Start with the highest-impact changes (caching, error handling, and concurrency control) and gradually implement the rest as needed.

Remember to monitor workflow performance after making changes to ensure they have the desired effect. GitHub Actions provides detailed logs and metrics that can help you identify further optimization opportunities.