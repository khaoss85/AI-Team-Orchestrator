# ⚠️ DEPRECATION NOTICE

## start_simple.py is DEPRECATED

**Effective Date**: 2025-06-12

### What's Deprecated
- `start_simple.py` - Simple backend server (port 8002)
- All references to port 8002 in documentation
- "Simple mode" server configuration

### Why Deprecated
The main server (`main.py`) now provides:
- ✅ **All functionality** from simple server
- ✅ **Additional features**: Goal validation, quality gates, AI improvements
- ✅ **Better performance**: Single server, no dual maintenance
- ✅ **Complete integration**: Real-time goal tracking, human verification

### Migration Guide

#### ❌ Old Way (DEPRECATED)
```bash
cd backend
python start_simple.py  # Runs on port 8002
```

#### ✅ New Way (RECOMMENDED)
```bash
cd backend
python main.py  # Runs on port 8000
```

### Frontend Changes
The frontend has been updated to use port 8000 by default:
- ✅ `api.ts` now points to `http://localhost:8000`
- ✅ All endpoints available
- ✅ No breaking changes

### What Happens If You Try to Use start_simple.py
The deprecated server will:
1. Show a deprecation warning
2. List migration instructions
3. Exit after 10 seconds

### Full Feature Comparison

| Feature | start_simple.py (DEPRECATED) | main.py (CURRENT) |
|---------|------------------------------|-------------------|
| Basic CRUD Operations | ✅ | ✅ |
| Workspace Management | ✅ | ✅ |
| Agent Management | ✅ | ✅ |
| Task Monitoring | ✅ | ✅ |
| Human Feedback | ✅ | ✅ |
| **Goal Validation** | ❌ | ✅ |
| **Quality Gates** | ❌ | ✅ |
| **AI Improvements** | ❌ | ✅ |
| **Real-time Goal Tracking** | ❌ | ✅ |
| **Human Verification** | ❌ | ✅ |
| **Course Correction** | ❌ | ✅ |

### Support Timeline
- **Immediate**: Deprecation warning added
- **Next Release**: File will be removed completely
- **Support**: No bug fixes or updates for start_simple.py

### Questions?
If you encounter issues migrating from start_simple.py to main.py, please:
1. Ensure you're using port 8000 instead of 8002
2. Verify all environment variables are set correctly
3. Check that the main server is running with `python main.py`

**The main server provides superior functionality and performance. Please migrate immediately.**