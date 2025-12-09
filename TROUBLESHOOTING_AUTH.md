# Authentication Troubleshooting Guide

## Issue: Getting 401 error when trying to login

### Backend Status: ✅ WORKING
- Admin user created: `admin` / `admin123`
- JWT endpoint tested with curl: ✅ Returns tokens
- JWT endpoint tested with Python requests: ✅ Returns tokens

### Possible Causes:

## 1. Backend Server Not Running

**Check:**
```bash
cd backend
python manage.py runserver
```

Should see:
```
Starting development server at http://127.0.0.1:8000/
```

## 2. CORS Issues

**Symptom:** Browser console shows CORS error

**Fix:** CORS is already configured in `backend/core/settings.py`:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:5173",
]
```

**If frontend runs on different port**, add it to `CORS_ALLOWED_ORIGINS`

## 3. Frontend API Base URL

**Check:** `frontend/src/lib/api.ts` line 1-2:
```typescript
export const API_BASE =
  import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";
```

**Create** `frontend/.env.local` if needed:
```
VITE_API_BASE=http://127.0.0.1:8000
```

## 4. Network/Firewall

**Test direct API call:**
```bash
curl -X POST http://127.0.0.1:8000/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

Should return:
```json
{
  "refresh": "eyJ...",
  "access": "eyJ..."
}
```

## 5. Browser DevTools Check

### Open Browser Console (F12)

**Check Network Tab:**
1. Go to Network tab
2. Try to login
3. Find the request to `/auth/token/`
4. Check:
   - Request Method: POST
   - Request Headers: Content-Type: application/json
   - Request Payload: `{"username":"admin","password":"admin123"}`
   - Response Status: Should be 200, not 401

**If Status is 401:**
- Check Response body for specific error
- Check if username/password are being sent correctly

**If No request shows:**
- Check Console tab for JavaScript errors
- Frontend might not be sending the request

## 6. Test Login Function Directly

**Open Browser Console on login page:**
```javascript
// Test API directly
fetch('http://127.0.0.1:8000/auth/token/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'admin', password: 'admin123' })
})
.then(r => r.json())
.then(d => console.log('Success:', d))
.catch(e => console.error('Error:', e))
```

Should log:
```
Success: {refresh: "eyJ...", access: "eyJ..."}
```

## 7. Common Error Messages

### "Authentication credentials were not provided or are invalid"
- This is the custom error handler generic message
- Real issue could be:
  - Wrong username/password
  - Malformed request
  - CORS blocking request

### "Session expired. Please login again"
- Happens when token refresh fails
- Try clearing localStorage and login again

### Network Error
- Backend not running
- Wrong URL
- Firewall/antivirus blocking

## Quick Fix Steps

### Step 1: Verify Backend
```bash
cd backend
python manage.py runserver
```

Keep this running.

### Step 2: Verify Admin User
```bash
cd backend
python manage.py shell
```

```python
from django.contrib.auth.models import User
admin = User.objects.get(username='admin')
admin.check_password('admin123')  # Should print: True
```

### Step 3: Test API Directly
```bash
curl -X POST http://127.0.0.1:8000/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### Step 4: Start Frontend
```bash
cd frontend
npm run dev
```

### Step 5: Open Browser DevTools
1. Open http://localhost:5173
2. Press F12 (DevTools)
3. Go to Network tab
4. Try to login
5. Check the `/auth/token/` request

### Step 6: Check for Errors
- Console tab: JavaScript errors?
- Network tab: Request sent? What response?

## Still Not Working?

### Enable Debug Logging

**Backend** (`backend/core/settings.py`):
```python
DEBUG = True

LOGGING = {
    # ... existing config
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',  # Change to DEBUG
        },
    },
}
```

**Frontend** (Browser Console):
Add before login attempt:
```javascript
localStorage.setItem('debug', 'true');
```

### Clear Everything
```bash
# Clear browser data
- Open DevTools (F12)
- Application tab
- Storage → Clear site data

# Or just clear localStorage
localStorage.clear()
```

### Create New Admin User
```bash
cd backend
python manage.py createsuperuser
```

Use different credentials and try again.

## Success Indicators

✅ Backend runs on port 8000
✅ Frontend runs on port 5173
✅ curl test returns tokens
✅ Browser Network tab shows 200 response
✅ localStorage has `access_token` and `refresh_token`
✅ Redirected to dashboard after login

## Contact

If still having issues, check:
1. Browser console screenshot
2. Network tab screenshot showing the failed request
3. Backend terminal output
