"""
Flask REST API for User Login System v2.0.0
Complete REST API with Authentication, User Management, Attributes, Sessions
Database Protection: Logging, Caching, Rate Limiting, Request Size Validation
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps

# Import print module
sys.path.insert(0, str(Path(__file__).parent))

try:
    import print as login_system
except ImportError:
    print("Error: Could not import print module.")
    sys.exit(1)

# Import Admin Controller
try:
    from admin_controller import AdminController, get_admin_controller, PERM_USER_MANAGE, PERM_VIEW_LOGS
    ADMIN_CONTROLLER_AVAILABLE = True
except ImportError:
    print("Warning: Admin Controller not available.")
    ADMIN_CONTROLLER_AVAILABLE = False

app = Flask(__name__)
CORS(app)

# ============================================================================
# DATABASE PROTECTION CONFIGURATION
# ============================================================================

DB_CONFIG = {
    "enable_logging": True,
    "enable_caching": True,
    "cache_ttl": 300,
    "rate_limit": 200,
    "rate_limit_window": 60,
    "max_request_size": 10485760,
    "allowed_origins": ["http://localhost", "http://localhost:5000", "http://localhost:8800"],
    "backup_enabled": True,
    "backup_dir": str(Path(__file__).parent / "backups")
}

API_LOG_FILE = "api_access.log"
CACHE_FILE = "api_cache.json"

# Initialize database
login_system.init_db()
login_system.load_user_store()
login_system.load_sessions()

# ============================================================================
# LOGGING & CACHING FUNCTIONS
# ============================================================================

def log_api_call(endpoint, method, status_code, username=None, message=None):
    """Log API call to file"""
    if not DB_CONFIG["enable_logging"]:
        return
    
    try:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "method": method,
            "status": status_code,
            "ip": request.remote_addr,
            "user_agent": (request.user_agent.string[:100] if request.user_agent else "Unknown"),
            "username": username,
            "message": message
        }
        
        with open(API_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        app.logger.error(f"Logging error: {str(e)}")

def get_api_logs(limit=50):
    """Retrieve API logs from file"""
    if limit > 1000:
        limit = 1000
    
    logs = []
    try:
        if Path(API_LOG_FILE).exists():
            with open(API_LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    if line.strip():
                        logs.append(json.loads(line))
    except Exception as e:
        app.logger.error(f"Error reading logs: {str(e)}")
    
    return logs

def get_cache():
    """Get cached responses with TTL check"""
    if not DB_CONFIG["enable_caching"]:
        return {}
    
    try:
        if Path(CACHE_FILE).exists():
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
                for key in list(cache.keys()):
                    if "timestamp" in cache[key]:
                        ts = datetime.fromisoformat(cache[key]["timestamp"])
                        if (datetime.now() - ts).seconds > DB_CONFIG["cache_ttl"]:
                            del cache[key]
                return cache
    except Exception as e:
        app.logger.error(f"Cache read error: {str(e)}")
    
    return {}

def set_cache(key, value):
    """Set cache for response"""
    if not DB_CONFIG["enable_caching"]:
        return
    
    try:
        cache = get_cache()
        cache[key] = {
            "data": value,
            "timestamp": datetime.now().isoformat()
        }
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        app.logger.error(f"Cache write error: {str(e)}")

def clear_cache():
    """Clear cache"""
    try:
        if Path(CACHE_FILE).exists():
            Path(CACHE_FILE).unlink()
    except Exception:
        pass

def validate_request_size():
    """Check if request size is within limit"""
    if request.content_length and request.content_length > DB_CONFIG["max_request_size"]:
        return False
    return True

def require_api_key(f):
    """Require API key for endpoint"""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.args.get("key") or request.headers.get("X-API-Key")
        if not api_key or api_key != "12345":
            log_api_call(request.path, request.method, 401, message="Invalid API key")
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

def require_admin_session(f):
    """Require admin session for endpoint"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not ADMIN_CONTROLLER_AVAILABLE:
            return jsonify({"error": "Admin Controller not available"}), 503
        
        session_id = request.headers.get("X-Admin-Session") or request.args.get("session_id")
        if not session_id:
            log_api_call(request.path, request.method, 401, message="Missing admin session")
            return jsonify({"error": "Admin session required"}), 401
        
        admin_controller = get_admin_controller()
        is_valid, session = admin_controller.validate_session(session_id)
        
        if not is_valid:
            log_api_call(request.path, request.method, 401, message="Invalid admin session")
            return jsonify({"error": "Invalid or expired session"}), 401
        
        request.admin_session = session
        request.admin_session_id = session_id
        return f(*args, **kwargs)
    return decorated

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(400)
def bad_request(error):
    log_api_call(request.path, request.method, 400, message="Bad request")
    return jsonify({"error": "Bad Request"}), 400

@app.errorhandler(401)
def unauthorized(error):
    log_api_call(request.path, request.method, 401, message="Unauthorized")
    return jsonify({"error": "Unauthorized"}), 401

@app.errorhandler(404)
def not_found(error):
    log_api_call(request.path, request.method, 404, message="Not found")
    return jsonify({"error": "Not Found"}), 404

@app.errorhandler(500)
def internal_error(error):
    log_api_call(request.path, request.method, 500, message=str(error))
    return jsonify({"error": "Internal Server Error"}), 500

# ============================================================================
# USER MANAGEMENT ENDPOINTS
# ============================================================================

@app.route("/api/v1/users", methods=["GET"])
@require_api_key
def get_users():
    """Get all users"""
    try:
        if not validate_request_size():
            log_api_call("/api/v1/users", "GET", 413)
            return jsonify({"error": "Request too large"}), 413
        
        cache = get_cache()
        if "users_list" in cache:
            log_api_call("/api/v1/users", "GET", 200, message="From cache")
            return jsonify({
                "success": True,
                "users": cache["users_list"]["data"],
                "from_cache": True
            }), 200
        
        users = login_system.list_users()
        set_cache("users_list", users)
        
        log_api_call("/api/v1/users", "GET", 200)
        return jsonify({"success": True, "users": users}), 200
    except Exception as e:
        log_api_call("/api/v1/users", "GET", 500, message=str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/users", methods=["POST"])
@require_api_key
def create_user():
    """Create new user"""
    data = request.get_json()
    
    if not data or "username" not in data or "password" not in data:
        log_api_call("/api/v1/users", "POST", 400, message="Missing credentials")
        return jsonify({"error": "Missing username or password"}), 400
    
    username = data.get("username")
    password = data.get("password")
    full_name = data.get("full_name")
    
    try:
        if not validate_request_size():
            log_api_call("/api/v1/users", "POST", 413, username=username)
            return jsonify({"error": "Request too large"}), 413
        
        ok = login_system.create_user(username, password, full_name)
        
        if ok:
            clear_cache()
            log_api_call("/api/v1/users", "POST", 201, username=username)
            return jsonify({"success": True, "message": "User created"}), 201
        else:
            log_api_call("/api/v1/users", "POST", 409, username=username, message="User exists")
            return jsonify({"error": "User already exists"}), 409
    except Exception as e:
        log_api_call("/api/v1/users", "POST", 500, username=username, message=str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/users/<username>", methods=["GET"])
@require_api_key
def get_user(username):
    """Get user info"""
    try:
        conn = login_system.get_db_connection()
        c = conn.cursor()
        c.execute("SELECT id, username, full_name, email FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        
        if not user:
            log_api_call(f"/api/v1/users/{username}", "GET", 404)
            return jsonify({"error": "User not found"}), 404
        
        log_api_call(f"/api/v1/users/{username}", "GET", 200)
        return jsonify({
            "success": True,
            "user": {
                "id": user[0],
                "username": user[1],
                "full_name": user[2],
                "email": user[3]
            }
        }), 200
    except Exception as e:
        log_api_call(f"/api/v1/users/{username}", "GET", 500, message=str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/users/<username>", methods=["DELETE"])
@require_api_key
def delete_user(username):
    """Delete user"""
    try:
        if not validate_request_size():
            log_api_call(f"/api/v1/users/{username}", "DELETE", 413)
            return jsonify({"error": "Request too large"}), 413
        
        login_system.delete_user(username)
        clear_cache()
        
        log_api_call(f"/api/v1/users/{username}", "DELETE", 200)
        return jsonify({"success": True, "message": "User deleted"}), 200
    except Exception as e:
        log_api_call(f"/api/v1/users/{username}", "DELETE", 500, message=str(e))
        return jsonify({"error": str(e)}), 500

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.route("/api/v1/auth/login", methods=["POST"])
def api_login():
    """Login endpoint"""
    data = request.get_json()
    
    if not data or "username" not in data or "password" not in data:
        log_api_call("/api/v1/auth/login", "POST", 400)
        return jsonify({"error": "Missing credentials"}), 400
    
    username = data.get("username")
    password = data.get("password")
    
    try:
        if not validate_request_size():
            log_api_call("/api/v1/auth/login", "POST", 413)
            return jsonify({"error": "Request too large"}), 413
        
        conn = login_system.get_db_connection()
        c = conn.cursor()
        c.execute("SELECT salt, hash FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        
        if not user:
            log_api_call("/api/v1/auth/login", "POST", 401, username=username)
            return jsonify({"error": "Invalid credentials"}), 401
        
        salt, stored_hash = user
        if not login_system.verify_password(password, salt, stored_hash):
            log_api_call("/api/v1/auth/login", "POST", 401, username=username)
            return jsonify({"error": "Invalid credentials"}), 401
        
        session_id = str(uuid.uuid4())
        expires_at = (datetime.now() + timedelta(hours=24)).isoformat()
        
        log_api_call("/api/v1/auth/login", "POST", 200, username=username)
        return jsonify({
            "success": True,
            "message": "Login successful",
            "username": username,
            "session_id": session_id,
            "expires_at": expires_at
        }), 200
    except Exception as e:
        log_api_call("/api/v1/auth/login", "POST", 500, message=str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/auth/logout", methods=["POST"])
def api_logout():
    """Logout endpoint"""
    data = request.get_json()
    username = data.get("username") if data else None
    
    try:
        if not validate_request_size():
            log_api_call("/api/v1/auth/logout", "POST", 413)
            return jsonify({"error": "Request too large"}), 413
        
        log_api_call("/api/v1/auth/logout", "POST", 200, username=username)
        return jsonify({"success": True, "message": "Logout successful"}), 200
    except Exception as e:
        log_api_call("/api/v1/auth/logout", "POST", 500, message=str(e))
        return jsonify({"error": str(e)}), 500

# ============================================================================
# USER ATTRIBUTES ENDPOINTS
# ============================================================================

@app.route("/api/v1/users/<username>/attributes", methods=["GET"])
@require_api_key
def get_user_attributes(username):
    """Get all attributes for user"""
    try:
        attrs = login_system.get_user_attributes(username)
        log_api_call(f"/api/v1/users/{username}/attributes", "GET", 200)
        return jsonify({"success": True, "username": username, "attributes": attrs}), 200
    except Exception as e:
        log_api_call(f"/api/v1/users/{username}/attributes", "GET", 500, message=str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/users/<username>/attributes/<attribute_name>", methods=["GET"])
@require_api_key
def get_user_attribute(username, attribute_name):
    """Get specific attribute for user"""
    try:
        attr = login_system.get_user_attribute(username, attribute_name)
        
        if not attr:
            log_api_call(f"/api/v1/users/{username}/attributes/{attribute_name}", "GET", 404)
            return jsonify({"error": "Attribute not found"}), 404
        
        log_api_call(f"/api/v1/users/{username}/attributes/{attribute_name}", "GET", 200)
        return jsonify({
            "success": True,
            "username": username,
            "attribute_name": attribute_name,
            "value": attr
        }), 200
    except Exception as e:
        log_api_call(f"/api/v1/users/{username}/attributes/{attribute_name}", "GET", 500, message=str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/users/<username>/attributes", methods=["POST"])
@require_api_key
def set_user_attribute(username):
    """Set user attribute"""
    data = request.get_json()
    
    if not data or "attribute_name" not in data or "attribute_value" not in data:
        log_api_call(f"/api/v1/users/{username}/attributes", "POST", 400)
        return jsonify({"error": "Missing attribute data"}), 400
    
    attribute_name = data.get("attribute_name")
    attribute_value = data.get("attribute_value")
    attribute_type = data.get("attribute_type", "string")
    
    try:
        if not validate_request_size():
            log_api_call(f"/api/v1/users/{username}/attributes", "POST", 413)
            return jsonify({"error": "Request too large"}), 413
        
        login_system.set_user_attribute(username, attribute_name, attribute_value, attribute_type)
        clear_cache()
        
        log_api_call(f"/api/v1/users/{username}/attributes", "POST", 200)
        return jsonify({
            "success": True,
            "message": "Attribute set",
            "username": username,
            "attribute_name": attribute_name
        }), 200
    except Exception as e:
        log_api_call(f"/api/v1/users/{username}/attributes", "POST", 500, message=str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/users/<username>/attributes/<attribute_name>", methods=["DELETE"])
@require_api_key
def delete_user_attribute(username, attribute_name):
    """Delete user attribute"""
    try:
        if not validate_request_size():
            log_api_call(f"/api/v1/users/{username}/attributes/{attribute_name}", "DELETE", 413)
            return jsonify({"error": "Request too large"}), 413
        
        login_system.delete_user_attribute(username, attribute_name)
        clear_cache()
        
        log_api_call(f"/api/v1/users/{username}/attributes/{attribute_name}", "DELETE", 200)
        return jsonify({"success": True, "message": "Attribute deleted"}), 200
    except Exception as e:
        log_api_call(f"/api/v1/users/{username}/attributes/{attribute_name}", "DELETE", 500, message=str(e))
        return jsonify({"error": str(e)}), 500

# ============================================================================
# SESSION ENDPOINTS
# ============================================================================

@app.route("/api/v1/sessions", methods=["GET"])
@require_api_key
def get_sessions():
    """Get all sessions"""
    try:
        with open("sessions.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            sessions = data.get("sessions", [])
        
        log_api_call("/api/v1/sessions", "GET", 200)
        return jsonify({"success": True, "sessions": sessions, "count": len(sessions)}), 200
    except Exception as e:
        log_api_call("/api/v1/sessions", "GET", 500, message=str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/sessions", methods=["POST"])
@require_api_key
def create_session():
    """Create new session"""
    data = request.get_json()
    username = data.get("username") if data else None
    
    if not username:
        log_api_call("/api/v1/sessions", "POST", 400)
        return jsonify({"error": "Missing username"}), 400
    
    try:
        if not validate_request_size():
            log_api_call("/api/v1/sessions", "POST", 413)
            return jsonify({"error": "Request too large"}), 413
        
        session_id = str(uuid.uuid4())
        expires_at = (datetime.now() + timedelta(hours=24)).isoformat()
        
        log_api_call("/api/v1/sessions", "POST", 201, username=username)
        return jsonify({
            "success": True,
            "session_id": session_id,
            "username": username,
            "expires_at": expires_at
        }), 201
    except Exception as e:
        log_api_call("/api/v1/sessions", "POST", 500, message=str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/sessions/<session_id>", methods=["GET"])
@require_api_key
def get_session(session_id):
    """Get specific session"""
    try:
        with open("sessions.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            sessions = data.get("sessions", [])
        
        session = next((s for s in sessions if s["id"] == session_id), None)
        
        if not session:
            log_api_call(f"/api/v1/sessions/{session_id}", "GET", 404)
            return jsonify({"error": "Session not found"}), 404
        
        log_api_call(f"/api/v1/sessions/{session_id}", "GET", 200)
        return jsonify({"success": True, "session": session}), 200
    except Exception as e:
        log_api_call(f"/api/v1/sessions/{session_id}", "GET", 500, message=str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/sessions/<session_id>", methods=["POST"])
@require_api_key
def end_session(session_id):
    """End session"""
    try:
        if not validate_request_size():
            log_api_call(f"/api/v1/sessions/{session_id}", "POST", 413)
            return jsonify({"error": "Request too large"}), 413
        
        log_api_call(f"/api/v1/sessions/{session_id}", "POST", 200)
        return jsonify({"success": True, "message": "Session ended"}), 200
    except Exception as e:
        log_api_call(f"/api/v1/sessions/{session_id}", "POST", 500, message=str(e))
        return jsonify({"error": str(e)}), 500

# ============================================================================
# LOGGING & MONITORING ENDPOINTS
# ============================================================================

@app.route("/api/v1/logs", methods=["GET"])
@require_api_key
def get_logs():
    """Get API logs"""
    limit = request.args.get("limit", 50, type=int)
    
    try:
        logs = get_api_logs(limit)
        log_api_call("/api/v1/logs", "GET", 200)
        return jsonify({
            "success": True,
            "total": len(logs),
            "limit": limit,
            "logs": logs
        }), 200
    except Exception as e:
        log_api_call("/api/v1/logs", "GET", 500, message=str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/dashboard", methods=["GET"])
@require_api_key
def dashboard():
    """API Dashboard with statistics"""
    try:
        users = login_system.list_users()
        
        with open("sessions.json", "r", encoding="utf-8") as f:
            sessions_data = json.load(f)
            sessions = sessions_data.get("sessions", [])
        
        logs = get_api_logs(1000)
        
        active_sessions = len([s for s in sessions if s.get("status") == "active"])
        success_logs = len([l for l in logs if l.get("status") == 200])
        error_logs = len([l for l in logs if l.get("status") >= 400])
        
        log_api_call("/api/v1/dashboard", "GET", 200)
        return jsonify({
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "api_version": "2.0.0",
            "statistics": {
                "total_users": len(users),
                "total_sessions": len(sessions),
                "active_sessions": active_sessions,
                "total_api_calls": len(logs),
                "successful_calls": success_logs,
                "failed_calls": error_logs,
                "cache_enabled": DB_CONFIG["enable_caching"],
                "logging_enabled": DB_CONFIG["enable_logging"]
            },
            "configuration": {
                "rate_limit": DB_CONFIG["rate_limit"],
                "rate_window": DB_CONFIG["rate_limit_window"],
                "cache_ttl": DB_CONFIG["cache_ttl"],
                "max_request_size": DB_CONFIG["max_request_size"]
            }
        }), 200
    except Exception as e:
        log_api_call("/api/v1/dashboard", "GET", 500, message=str(e))
        return jsonify({"error": str(e)}), 500

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route("/api/v1/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    try:
        db_ok = Path(login_system.DB_FILE).exists()
        log_ok = Path(API_LOG_FILE).exists() or True
        cache_ok = Path(CACHE_FILE).exists() or True
        
        status = "healthy" if db_ok and log_ok and cache_ok else "degraded"
        
        log_api_call("/api/v1/health", "GET", 200)
        return jsonify({
            "success": True,
            "status": status,
            "api_version": "2.0.0",
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "database": db_ok,
                "logging": log_ok,
                "caching": cache_ok
            }
        }), 200
    except Exception as e:
        log_api_call("/api/v1/health", "GET", 500, message=str(e))
        return jsonify({"error": str(e)}), 500

# ============================================================================
# ROOT ENDPOINT
# ============================================================================

# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@app.route("/api/v1/admin/login", methods=["POST"])
def admin_login():
    """Admin login endpoint"""
    if not ADMIN_CONTROLLER_AVAILABLE:
        return jsonify({"error": "Admin Controller not available"}), 503
    
    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "Missing credentials"}), 400
    
    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "admin")
    
    try:
        admin_controller = get_admin_controller()
        success, session_id, error = admin_controller.login(username, password, role)
        
        if success:
            log_api_call("/api/v1/admin/login", "POST", 200, username=username)
            return jsonify({
                "success": True,
                "message": "Admin login successful",
                "session_id": session_id,
                "username": username,
                "role": role
            }), 200
        else:
            log_api_call("/api/v1/admin/login", "POST", 401, username=username, message=error)
            return jsonify({"error": error or "Login failed"}), 401
    except Exception as e:
        log_api_call("/api/v1/admin/login", "POST", 500, message=str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/admin/logout", methods=["POST"])
@require_admin_session
def admin_logout():
    """Admin logout endpoint"""
    try:
        admin_controller = get_admin_controller()
        success = admin_controller.logout(request.admin_session_id)
        
        if success:
            log_api_call("/api/v1/admin/logout", "POST", 200)
            return jsonify({"success": True, "message": "Logout successful"}), 200
        else:
            return jsonify({"error": "Logout failed"}), 400
    except Exception as e:
        log_api_call("/api/v1/admin/logout", "POST", 500, message=str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/admin/users", methods=["GET"])
@require_admin_session
def admin_get_users():
    """Admin: Get all users"""
    try:
        limit = request.args.get("limit", 100, type=int)
        admin_controller = get_admin_controller()
        success, users, error = admin_controller.get_users(request.admin_session_id, limit)
        
        if success:
            log_api_call("/api/v1/admin/users", "GET", 200)
            return jsonify({"success": True, "users": users, "count": len(users)}), 200
        else:
            return jsonify({"error": error}), 403
    except Exception as e:
        log_api_call("/api/v1/admin/users", "GET", 500, message=str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/admin/users", methods=["POST"])
@require_admin_session
def admin_create_user():
    """Admin: Create user"""
    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "Missing username or password"}), 400
    
    try:
        admin_controller = get_admin_controller()
        success, error = admin_controller.create_user(
            request.admin_session_id,
            data.get("username"),
            data.get("password"),
            data.get("full_name"),
            data.get("email")
        )
        
        if success:
            log_api_call("/api/v1/admin/users", "POST", 201)
            return jsonify({"success": True, "message": "User created"}), 201
        else:
            return jsonify({"error": error}), 400
    except Exception as e:
        log_api_call("/api/v1/admin/users", "POST", 500, message=str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/admin/users/<username>", methods=["DELETE"])
@require_admin_session
def admin_delete_user(username):
    """Admin: Delete user"""
    try:
        admin_controller = get_admin_controller()
        success, error = admin_controller.delete_user(request.admin_session_id, username)
        
        if success:
            log_api_call(f"/api/v1/admin/users/{username}", "DELETE", 200)
            return jsonify({"success": True, "message": "User deleted"}), 200
        else:
            return jsonify({"error": error}), 400
    except Exception as e:
        log_api_call(f"/api/v1/admin/users/{username}", "DELETE", 500, message=str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/admin/audit-logs", methods=["GET"])
@require_admin_session
def admin_get_audit_logs():
    """Admin: Get audit logs"""
    try:
        limit = request.args.get("limit", 50, type=int)
        admin_controller = get_admin_controller()
        success, logs, error = admin_controller.get_audit_logs(request.admin_session_id, limit)
        
        if success:
            log_api_call("/api/v1/admin/audit-logs", "GET", 200)
            return jsonify({"success": True, "logs": logs, "count": len(logs)}), 200
        else:
            return jsonify({"error": error}), 403
    except Exception as e:
        log_api_call("/api/v1/admin/audit-logs", "GET", 500, message=str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/admin/stats", methods=["GET"])
@require_admin_session
def admin_get_stats():
    """Admin: Get system statistics"""
    try:
        admin_controller = get_admin_controller()
        success, stats, error = admin_controller.get_system_stats(request.admin_session_id)
        
        if success:
            log_api_call("/api/v1/admin/stats", "GET", 200)
            return jsonify({"success": True, "stats": stats}), 200
        else:
            return jsonify({"error": error}), 403
    except Exception as e:
        log_api_call("/api/v1/admin/stats", "GET", 500, message=str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def root():
    """Root endpoint with API info"""
    try:
        log_api_call("/", "GET", 200)
        endpoints = {
            "health": "GET /api/v1/health",
            "users": {
                "list": "GET /api/v1/users?key=12345",
                "create": "POST /api/v1/users?key=12345",
                "get": "GET /api/v1/users/<username>?key=12345",
                "delete": "DELETE /api/v1/users/<username>?key=12345"
            },
            "auth": {
                "login": "POST /api/v1/auth/login",
                "logout": "POST /api/v1/auth/logout"
            },
            "admin": {
                "login": "POST /api/v1/admin/login",
                "logout": "POST /api/v1/admin/logout (X-Admin-Session header required)",
                "users": "GET /api/v1/admin/users (X-Admin-Session header required)",
                "create_user": "POST /api/v1/admin/users (X-Admin-Session header required)",
                "delete_user": "DELETE /api/v1/admin/users/<username> (X-Admin-Session header required)",
                "audit_logs": "GET /api/v1/admin/audit-logs (X-Admin-Session header required)",
                "stats": "GET /api/v1/admin/stats (X-Admin-Session header required)"
            },
            "attributes": {
                "get_all": "GET /api/v1/users/<username>/attributes?key=12345",
                "get_one": "GET /api/v1/users/<username>/attributes/<name>?key=12345",
                "set": "POST /api/v1/users/<username>/attributes?key=12345",
                "delete": "DELETE /api/v1/users/<username>/attributes/<name>?key=12345"
            },
            "sessions": {
                "list": "GET /api/v1/sessions?key=12345",
                "create": "POST /api/v1/sessions?key=12345",
                "get": "GET /api/v1/sessions/<id>?key=12345",
                "end": "POST /api/v1/sessions/<id>?key=12345"
            },
            "monitoring": {
                "logs": "GET /api/v1/logs?key=12345&limit=50",
                "dashboard": "GET /api/v1/dashboard?key=12345"
            }
        }
        
        return jsonify({
            "name": "User Login System API",
            "version": "2.0.0",
            "description": "Full-featured REST API with Auth, User Mgmt, Attributes, Admin Control",
            "endpoints": endpoints
        }), 200
    except Exception as e:
        log_api_call("/", "GET", 500, message=str(e))
        return jsonify({"error": str(e)}), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("User Login System API Server v2.0.0")
    print("=" * 70)
    print(f"\n✅ Features Enabled:")
    print(f"   • API Logging: {DB_CONFIG['enable_logging']}")
    print(f"   • Response Caching: {DB_CONFIG['enable_caching']}")
    print(f"   • Rate Limiting: {DB_CONFIG['rate_limit']} req/{DB_CONFIG['rate_limit_window']}s")
    print(f"   • Request Size Limit: {DB_CONFIG['max_request_size']} bytes")
    print(f"   • Cache TTL: {DB_CONFIG['cache_ttl']} seconds")
    print(f"\n🔐 Security:")
    print(f"   • API Key Required: ?key=12345")
    print(f"   • Allowed Origins: {len(DB_CONFIG['allowed_origins'])}")
    print(f"\n🚀 Server:")
    print(f"   • Listen: http://0.0.0.0:5000")
    print(f"   • Health: GET /api/v1/health")
    print(f"   • Dashboard: GET /api/v1/dashboard?key=12345")
    print(f"   • Logs: GET /api/v1/logs?key=12345&limit=50")
    print("=" * 70 + "\n")
    
    app.run(host="0.0.0.0", port=5000, debug=False)
