# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Start the Application
- **Development**: `python main.py` (starts on localhost:5000)
- **Production**: `gunicorn app:app` (use for production deployment)

### Database Operations
- **Initialize Database**: `python -c "from app import db; db.create_all()"`
- **Reset Database**: Remove `instance/chatbot.db` file and reinitialize
- **Database Migrations**: Tables are auto-created on app startup, including new caching tables

### Cache Population (Important for Complete Dashboard Coverage)
The system caches Looker metadata (models, explores, dashboards) in the database for improved performance and search accuracy. **For production deployments, you should populate the complete cache to ensure ALL dashboards are discoverable.**

#### Comprehensive Cache Population
- **Populate All Caches**: `python populate_cache.py --all` (recommended for initial setup)
- **Populate Specific Cache**: 
  - Models only: `python populate_cache.py --models`
  - Explores only: `python populate_cache.py --explores`  
  - Dashboards only: `python populate_cache.py --dashboards`
- **Force Refresh**: `python populate_cache.py --all --force` (ignores 24-hour cache TTL)
- **Verbose Output**: `python populate_cache.py --all --verbose` (detailed logging)

#### Why Use Cache Population?
- **Complete Dashboard Coverage**: Real-time queries only fetch first ~100 dashboards due to timeout constraints
- **Better Search Accuracy**: Pre-cached metadata enables sophisticated dashboard matching and business context analysis  
- **Production Performance**: Separates heavy data fetching from real-time user interactions
- **Scheduled Updates**: Run daily via cron to keep cache fresh: `0 2 * * * cd /path/to/app && python populate_cache.py --all`

#### Cache Population Schedule
```bash
# Add to crontab for daily refresh at 2 AM
0 2 * * * cd /path/to/chatbot && /path/to/python populate_cache.py --all >> /var/log/looker_cache.log 2>&1
```

**⚠️ Important**: Cache population automatically loads environment variables from your `.env` file. Ensure your `.env` file contains: LOOKER_BASE_URL, LOOKER_CLIENT_ID, LOOKER_CLIENT_SECRET, OPENAI_API_KEY.

### Dependencies
- **Install**: `uv sync` or `pip install -r requirements.txt`
- **Using UV**: This project is configured for UV package manager (see pyproject.toml)

### Testing
- **Run All Tests**: `python tests/run_tests.py` (runs all test suites)
- **Run Individual Tests**:
  - Direct Looker Query Test: `python tests/test_direct_query.py`
  - Chatbot Agent Test: `python tests/test_chatbot.py`
  - Basic Database Caching Test: `python tests/test_basic_caching.py` (no credentials needed)
  - Full Database Caching Test: `python tests/test_database_caching.py` (requires Looker credentials)
  - Semantic Search Test: `python tests/test_semantic_search.py` (tests field-level keyword matching)
  - Comprehensive Similarity Search Test: `python tests/test_similarity_search.py` (tests fuzzy model matching)
  - Dashboard Context Integration Test: `python tests/test_dashboard_context.py` (tests enhanced dashboard context system)
  - Dashboard Query Test: `python tests/test_dashboard_query.py` (tests dashboard-specific query handling with URLs)
  - Enhanced Model Selection Test: `python tests/test_improved_model_selection.py` (requires credentials)
  - Database Tables Test: `python tests/test_db_tables.py`
- **Test Requirements**: Ensure all environment variables are set before running tests

## Architecture Overview

### Core Components
- **app.py**: Main Flask application with all routes, authentication, and CORS setup
- **chat_agent.py**: LookerChatAgent class that interfaces with Looker BI via langchain-looker-agent
- **models.py**: SQLAlchemy models (User, ChatSession, ChatError) for database persistence
- **main.py**: Application entry point (imports from app.py)

### Database Models
- **User**: Authentication with per-user Looker credentials storage
- **ChatSession**: Conversation logging for analytics
- **ChatError**: Error tracking for monitoring
- **LookerModel**: Database caching of Looker model metadata (24-hour cache)
- **LookerExplore**: Database caching of Looker explore metadata with dimensions/measures (24-hour cache)
- **LookerDashboard**: Database caching of Looker dashboard metadata with business context (24-hour cache)
- **DashboardExploreMapping**: Business context mapping between dashboards and explores

### Frontend Architecture
- **Templates**: Jinja2 templates for login/register pages and demo interface
- **Static Assets**: Embeddable JavaScript widget (widget.js) and CSS (widget.css)
- **Widget Integration**: Standalone chatbot widget for embedding on external websites

### Authentication Flow
- Flask-Login with session-based authentication
- Per-user credential storage in database (Looker API keys, OpenAI keys)
- Both authenticated (database-stored) and widget (localStorage-based) credential handling

### Looker Integration
- Uses Looker SDK directly for BI queries and model discovery
- Automatic model and explore discovery - no manual model configuration required
- **Enhanced AI-powered model/explore selection** with multi-layered search:
  1. **Semantic Search**: Field-level keyword matching with cached metadata
  2. **Comprehensive Similarity Search**: Fuzzy matching across ALL models/explores when semantic search fails
  3. **Exact Model Queries**: Direct handling of "is there a model called X?" questions
- Intelligent keyword extraction and domain-specific term expansion (e.g., "ab test" → "experiment", "variant", "winner")
- Database caching of models and explores with detailed field metadata (24-hour cache refresh)
- Semantic scoring based on field names, descriptions, and explore metadata
- Fallback mechanisms ensure relevant suggestions even when exact matches aren't found
- Requires JDBC driver (looker-jdbc.jar) for database connections
- Dynamic agent creation based on user credentials or environment variables
- Chat history context maintained in Flask sessions

### Dashboard Query System (Enhanced Feature)
- **Dashboard-Specific Query Detection**: Automatically detects queries asking specifically about dashboards
  - Recognizes patterns: "is there a dashboard for X", "show me dashboards about Y", "find a dashboard for Z"
  - Highest priority routing ensures dashboard queries get specialized handling
- **Enhanced Dashboard Search & Matching**:
  - **Real-World Optimized Scoring**: Designed for production Looker instances with potentially empty descriptions
  - **Bi-Weekly Specific Matching**: Special handling for "bi-weekly", "biweekly", "bi weekly" queries
  - **Domain-Specific Recognition**: Cost/Finance, Experiments, User Analytics domain awareness
  - **Folder-Based Context**: Uses dashboard folders for business context scoring
  - **Penalty System**: Reduces relevance for obvious domain mismatches
- **Comprehensive Dashboard Response Format**:
  - Dashboard title with folder/space context
  - Business-friendly descriptions (when available)
  - **Direct clickable URLs** to actual Looker dashboards
  - Related explores for deeper analysis
  - Multiple relevant dashboard suggestions with ranking
- **Enhanced Dashboard Fetching**: 
  - Fetches comprehensive dashboard metadata including tags, folders, spaces
  - Increased limit (100+ dashboards) to ensure target dashboards aren't missed
  - Robust error handling for missing dashboard metadata
  - Debug logging for dashboard discovery and scoring

### API Endpoints
- `/api/chat`: Main chat processing with Looker agent
- `/api/auth/*`: Authentication endpoints (login/register/logout/status)
- `/api/settings`: User credential management
- `/api/test-connection`: Looker connection verification

### Test Architecture
- **tests/**: Centralized test directory containing all test scripts
- **test_direct_query.py**: Tests direct Looker SDK connectivity and dynamic model discovery
- **test_chatbot.py**: Tests the LookerChatAgent with various query scenarios including AI-powered model selection
- **test_database_caching.py**: Tests database caching functionality for models and explores
- **test_db_tables.py**: Tests database table creation including new caching tables
- **run_tests.py**: Test runner that executes all test suites sequentially
- All tests work without LOOKML_MODEL_NAME and require proper environment configuration (Looker + OpenAI credentials)

## Key Environment Variables

Required for Looker integration:
- `LOOKER_BASE_URL`: Looker instance URL
- `LOOKER_CLIENT_ID`: API client ID  
- `LOOKER_CLIENT_SECRET`: API client secret
- `OPENAI_API_KEY`: For natural language processing
- `JDBC_DRIVER_PATH`: Path to Looker JDBC driver JAR

**Note**: `LOOKML_MODEL_NAME` is no longer required - the system now automatically discovers and works with all available models using intelligent model selection based on user queries.

Optional:
- `DATABASE_URL`: PostgreSQL connection (defaults to SQLite)
- `SESSION_SECRET`: Flask session secret
- `JAVA_HOME`: Java installation path (for JDBC driver)

## Deployment Notes

### Database Configuration
- Development: SQLite (`instance/chatbot.db`)
- Production: PostgreSQL via `DATABASE_URL`
- Auto-creates tables on app startup

### CORS Configuration
- Configured for cross-domain widget embedding
- Supports credentials for authenticated sessions
- Allows all origins (adjust for production security)

### Error Handling
- Comprehensive error handling in chat_agent.py with user-friendly messages
- Database logging of errors and chat sessions
- Agent initialization failures handled gracefully

## Dashboard Query Troubleshooting

### Common Issues and Solutions

#### Issue: Dashboard queries return wrong/irrelevant dashboards
**Root Cause**: Target dashboard not being found or scored properly
**Solutions**:
1. **🔧 RECOMMENDED FIX: Use Complete Cache Population**
   - Run `python populate_cache.py --dashboards --force` to cache ALL dashboards
   - This eliminates the 100-dashboard limit that causes missing results
   - Schedule daily: `0 2 * * * cd /path/to/app && python populate_cache.py --all`

2. **Check Dashboard Fetching**: Verify the target dashboard is being retrieved from Looker API
   - Look for log message: `Key dashboard found - ID: {target_id}, Title: '{title}', Folder: '{folder}'`  
   - If missing, dashboard may be beyond the 100-dashboard fetch limit or have access restrictions

3. **Debug Dashboard Scoring**: Check logs for dashboard scoring information  
   - Look for: `Dashboard '{title}' scored {score} - {reason}`
   - Scores above 80 indicate high relevance, above 40 medium relevance

4. **Verify Keywords**: Ensure query keywords match dashboard titles/descriptions
   - "bi-weekly" should match dashboards with "bi-weekly", "biweekly", or "bi weekly" in title
   - "cost" should match dashboards with "cost", "finops", "billing", "finance" terms

#### Issue: Dashboard descriptions showing "No description available"
**Root Cause**: Looker API not returning description fields or dashboards lacking descriptions
**Solutions**:
1. **Relies on Title Matching**: System is optimized to work with title-only matching when descriptions are unavailable
2. **Folder Context**: Uses dashboard folder/space names for additional context
3. **Domain-Specific Logic**: Recognizes cost, experiment, and analytics domains from titles alone

#### Issue: Specific dashboard (e.g., ID 2659) not appearing in results
**🔧 RECOMMENDED FIX**: Run `python populate_cache.py --dashboards --force` to cache ALL dashboards from your Looker instance.

**Debugging Steps**:
1. **First, populate complete cache**: `python populate_cache.py --dashboards --force`
2. Check if dashboard is being fetched: Look for log `Key dashboard found - ID: 2659`
3. If still not found after cache population, dashboard may be:
   - In a restricted folder/space
   - Not accessible with current user permissions
   - Deleted or moved in Looker
4. If found but not in top results, check scoring logs to see why it scored low

### Performance Optimization
- **Real-time queries**: Dashboard fetching limited to ~100 dashboards to prevent API timeouts
- **Background cache population**: `populate_cache.py` script fetches ALL dashboards without timeout constraints
- **24-hour database caching**: Reduces API calls and improves response times
- **Scheduled refresh**: Daily cache population ensures fresh data without affecting user experience
- **Comprehensive error handling**: Graceful degradation when cache or API issues occur

### Cache Population Best Practices
1. **Initial Setup**: Run `python populate_cache.py --all` after deployment
2. **Production Schedule**: Set up daily cron job for cache refresh
3. **Monitoring**: Check logs for cache population success/failures
4. **Troubleshooting**: Use `--force` flag to bypass cache TTL when debugging