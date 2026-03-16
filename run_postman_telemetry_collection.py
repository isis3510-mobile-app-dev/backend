"""
End-to-end runner for Postman collection against live Django server.
Tests all non-auth endpoints (Screens CRUD, Features CRUD, FeatureRoutes CRUD,
plus GET for all log collections, plus auth-blocked POST checks).
"""
import json, urllib.request, urllib.error, sys

BASE = "http://127.0.0.1:8000/api"
RESULTS = []

def http(method, path, body=None, headers=None):
    url = f"{BASE}{path}"
    hdrs = {"Content-Type": "application/json"}
    if headers:
        hdrs.update(headers)
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            try:
                return resp.status, json.loads(raw)
            except:
                return resp.status, raw.decode()
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except:
            return e.code, raw.decode()

def check(name, expected_status, actual_status, body, extra_checks=None):
    ok = actual_status == expected_status
    checks_ok = True
    msgs = []
    if extra_checks:
        for desc, fn in extra_checks:
            try:
                result = fn(body)
                if not result:
                    checks_ok = False
                    msgs.append(f"  FAIL: {desc}")
            except Exception as ex:
                checks_ok = False
                msgs.append(f"  FAIL: {desc} ({ex})")

    passed = ok and checks_ok
    sym = "✅" if passed else "❌"
    print(f"  {sym} {name}  (expected={expected_status}, got={actual_status})")
    for m in msgs:
        print(m)
    RESULTS.append(passed)
    return body

# ──────────────────────────────────────────────────────────────────
print("=" * 60)
print("  SCREENS CRUD")
print("=" * 60)

# Create
s, body = http("POST", "/screens/", {
    "schema": 1, "name": "HomeScreen", "hasAds": False,
    "buttons": [
        {"buttonId": "btn_add_pet", "schema": 1, "name": "Add Pet"},
        {"buttonId": "btn_profile", "schema": 1, "name": "Profile"}
    ]
})
check("Create Screen", 201, s, body, [
    ("has id",      lambda b: "id" in b),
    ("has name",    lambda b: b["name"] == "HomeScreen"),
    ("has buttons", lambda b: len(b["buttons"]) == 2),
])
screen_id = body.get("id", "") if isinstance(body, dict) else ""

# List
s, body = http("GET", "/screens/")
check("List Screens", 200, s, body, [
    ("is array", lambda b: isinstance(b, list)),
    ("contains created screen", lambda b: any(x["id"] == screen_id for x in b)),
])

# Get by ID
s, body = http("GET", f"/screens/{screen_id}/")
check("Get Screen by ID", 200, s, body, [
    ("id matches", lambda b: b["id"] == screen_id),
])

# Update
s, body = http("PUT", f"/screens/{screen_id}/", {
    "schema": 1, "name": "HomeScreen v2", "hasAds": True,
    "buttons": [{"buttonId": "btn_add_pet", "schema": 1, "name": "Add Pet"}]
})
check("Update Screen", 200, s, body, [
    ("name updated",   lambda b: b["name"] == "HomeScreen v2"),
    ("hasAds updated", lambda b: b["hasAds"] == True),
    ("buttons shrunk", lambda b: len(b["buttons"]) == 1),
])

# Delete
s, body = http("DELETE", f"/screens/{screen_id}/")
check("Delete Screen", 204, s, body)

# Not Found
s, body = http("GET", "/screens/000000000000000000000000/")
check("Get Screen — 404", 404, s, body, [
    ("has error field", lambda b: "error" in b),
])

# ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  SCREEN TIME LOGS")
print("=" * 60)

# GET (no auth)
s, body = http("GET", "/screen-time-logs/")
check("List Screen Time Logs", 200, s, body, [
    ("is array", lambda b: isinstance(b, list)),
])

# POST without auth -> 401
s, body = http("POST", "/screen-time-logs/", {
    "userId": "000000000000000000000001",
    "screenId": "000000000000000000000002",
    "startTime": "2026-03-15T10:00:00Z",
    "endTime": "2026-03-15T10:02:30Z"
})
check("Create ScreenTimeLog — No Auth (401)", 401, s, body)

# ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  FEATURES CRUD")
print("=" * 60)

s, body = http("POST", "/features/", {
    "schema": 1, "name": "AddPetFeature",
    "originButton": "btn_add_pet",
    "originScreen": "000000000000000000000002",
    "appType": "Kotlin"
})
check("Create Feature", 201, s, body, [
    ("has id",   lambda b: "id" in b),
    ("has name", lambda b: b["name"] == "AddPetFeature"),
    ("appType",  lambda b: b["appType"] == "Kotlin"),
])
feature_id = body.get("id", "") if isinstance(body, dict) else ""

s, body = http("GET", "/features/")
check("List Features", 200, s, body, [
    ("is array", lambda b: isinstance(b, list)),
])

s, body = http("GET", f"/features/{feature_id}/")
check("Get Feature by ID", 200, s, body, [
    ("id matches", lambda b: b["id"] == feature_id),
])

s, body = http("PUT", f"/features/{feature_id}/", {
    "schema": 1, "name": "AddPetFeature v2",
    "originButton": "btn_add_pet",
    "originScreen": "000000000000000000000002",
    "appType": "Flutter"
})
check("Update Feature", 200, s, body, [
    ("name updated",    lambda b: b["name"] == "AddPetFeature v2"),
    ("appType updated", lambda b: b["appType"] == "Flutter"),
])

s, body = http("DELETE", f"/features/{feature_id}/")
check("Delete Feature", 204, s, body)

s, body = http("GET", "/features/000000000000000000000000/")
check("Get Feature — 404", 404, s, body, [
    ("has error", lambda b: "error" in b),
])

# ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  FEATURE ROUTES CRUD")
print("=" * 60)

s, body = http("POST", "/feature-routes/", {
    "schema": 1, "name": "HomeToAddPet",
    "originButton": "btn_add_pet", "originScreen": "000000000000000000000002",
    "endButton": "btn_confirm",    "endScreen": "000000000000000000000003"
})
check("Create Feature Route", 201, s, body, [
    ("has id",   lambda b: "id" in b),
    ("has name", lambda b: b["name"] == "HomeToAddPet"),
])
route_id = body.get("id", "") if isinstance(body, dict) else ""

s, body = http("GET", "/feature-routes/")
check("List Feature Routes", 200, s, body, [
    ("is array", lambda b: isinstance(b, list)),
])

s, body = http("GET", f"/feature-routes/{route_id}/")
check("Get Feature Route by ID", 200, s, body, [
    ("id matches", lambda b: b["id"] == route_id),
])

s, body = http("PUT", f"/feature-routes/{route_id}/", {
    "schema": 1, "name": "HomeToAddPet v2",
    "originButton": "btn_add_pet", "originScreen": "000000000000000000000002",
    "endButton": "btn_save",       "endScreen": "000000000000000000000004"
})
check("Update Feature Route", 200, s, body, [
    ("name updated", lambda b: b["name"] == "HomeToAddPet v2"),
])

s, body = http("DELETE", f"/feature-routes/{route_id}/")
check("Delete Feature Route", 204, s, body)

s, body = http("GET", "/feature-routes/000000000000000000000000/")
check("Get Feature Route — 404", 404, s, body, [
    ("has error", lambda b: "error" in b),
])

# ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  FEATURE EXECUTION LOGS")
print("=" * 60)

s, body = http("GET", "/feature-execution-logs/")
check("List Feature Execution Logs", 200, s, body, [
    ("is array", lambda b: isinstance(b, list)),
])

s, body = http("POST", "/feature-execution-logs/", {
    "userId": "000000000000000000000001",
    "featureId": "000000000000000000000005",
    "startTime": "2026-03-15T10:00:00Z",
    "endTime": "2026-03-15T10:00:05Z"
})
check("Create ExecLog — No Auth (401)", 401, s, body)

# ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  FEATURE CLICKS LOGS")
print("=" * 60)

s, body = http("GET", "/feature-clicks-logs/")
check("List Feature Clicks Logs", 200, s, body, [
    ("is array", lambda b: isinstance(b, list)),
])

s, body = http("POST", "/feature-clicks-logs/", {
    "userId": "000000000000000000000001",
    "routeId": "000000000000000000000006",
    "timestamp": "2026-03-15T10:05:00Z",
    "nClicks": 5
})
check("Create ClicksLog — No Auth (401)", 401, s, body)

# ──────────────────────────────────────────────────────────────────
total = len(RESULTS)
passed = sum(RESULTS)
print("\n" + "=" * 60)
print(f"  RESULT: {passed}/{total} tests passed")
print("=" * 60)
sys.exit(0 if passed == total else 1)
