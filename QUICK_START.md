# Quick Start Guide

## Yes, you need to run all 3 microservices + the composite service!

The composite service delegates requests to the atomic services, so all 4 services must be running.

## Quick Start (4 Terminal Windows)

### Terminal 1: Integrations Service
```bash
cd /Users/ag/Desktop/final_project/integrations-svc-ms2

# Create .env file if it doesn't exist (required for this service)
if [ ! -f .env ]; then
  # Generate a valid Fernet key
  TOKEN_KEY=$(python3 -c "import base64, secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())")
  cat > .env << EOF
DATABASE_URL=sqlite+aiosqlite:///./dev.db
TOKEN_ENCRYPTION_KEY=${TOKEN_KEY}
EOF
fi

# Install dependencies (including aiosqlite for SQLite support)
pip install -r requirements.txt
python main.py
```
**Should show**: `Uvicorn running on http://0.0.0.0:8000`

### Terminal 2: Actions Service
```bash
cd /Users/ag/Desktop/final_project/ms3
pip install -r requirements.txt  # if not already installed
python main.py
```
**Should show**: `Uvicorn running on http://0.0.0.0:8004`

### Terminal 3: Classification Service
```bash
cd /Users/ag/Desktop/final_project/ms4-classification
pip install -r requirements.txt  # if not already installed
python main.py
```
**Should show**: `Uvicorn running on http://0.0.0.0:8001`

### Terminal 4: Composite Service
```bash
cd /Users/ag/Desktop/final_project/composite-ms1
pip install -r requirements.txt  # if not already installed
python main.py
```
**Should show**: 
```
INFO:     Starting Composite Microservice...
INFO:     Atomic services configured:
INFO:       - Integrations Service: http://localhost:8000
INFO:       - Actions Service: http://localhost:8004
INFO:       - Classification Service: http://localhost:8001
INFO:     Uvicorn running on http://0.0.0.0:8002
```

## Test It Works

### Option 1: Use the test script
```bash
cd /Users/ag/Desktop/final_project/composite-ms1
./test_composite.sh
```

### Option 2: Manual testing

1. **Check composite health** (checks all services):
   ```bash
   curl http://localhost:8002/health
   ```

2. **Check individual services through composite**:
   ```bash
   curl http://localhost:8002/api/integrations/health
   curl http://localhost:8002/api/actions/health
   curl http://localhost:8002/api/classification/health
   ```

3. **View API docs** (open in browser):
   - http://localhost:8002/docs

## What to Expect

✅ **Success**: All services return health status  
✅ **Success**: Composite service logs show requests to atomic services  
✅ **Success**: API docs show all endpoints  

❌ **Failure**: If you see "Connection refused" or "502 Bad Gateway", check:
- Are all 4 services running?
- Are they on the correct ports (8000, 8001, 8004, 8002)?
- Check the terminal logs for errors

## Port Summary

- **8000**: Integrations Service
- **8001**: Classification Service  
- **8004**: Actions Service
- **8002**: Composite Service (this one)

## Next Steps

Once all services are running:
1. Open http://localhost:8002/docs to see the API
2. Try some endpoints through the composite service
3. Check the composite service logs to see inter-service communication
4. See TESTING_GUIDE.md for more detailed testing

