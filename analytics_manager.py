#!/usr/bin/env python3
"""
analytics_manager.py — CLI for managing the PetCare analytics database.

Usage:
    python analytics_manager.py wipe --app-type Kotlin     # Wipe Kotlin analytics only
    python analytics_manager.py wipe --app-type Flutter    # Wipe Flutter analytics only
    python analytics_manager.py wipe --all                 # Wipe ALL analytics data

    python analytics_manager.py export                     # Export all collections to CSV
    python analytics_manager.py export --output-dir ./out  # Custom output directory
    python analytics_manager.py export --collections screens features  # Specific only
"""

import os
import sys
import csv
import argparse
from datetime import datetime

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django  # noqa: E402
django.setup()

from api.models import (  # noqa: E402
    User, Pet, Vaccine, Event, Notification,
    Screen, ScreenTimeLog, Feature, FeatureRoute,
    FeatureExecutionLog, FeatureClicksLog,
)


# ─── Wipe ────────────────────────────────────────────────────────────────────

ANALYTICS_MODELS_WITH_APP_TYPE = [
    ("Screen", Screen),
    ("Feature", Feature),
    ("FeatureRoute", FeatureRoute),
    ("ScreenTimeLog", ScreenTimeLog),
    ("FeatureExecutionLog", FeatureExecutionLog),
    ("FeatureClicksLog", FeatureClicksLog),
]


def cmd_wipe(args):
    """Delete analytics data, optionally filtered by appType."""
    if not args.all and not args.app_type:
        print("Error: You must specify --app-type <type> or --all")
        sys.exit(1)

    label = "ALL" if args.all else args.app_type
    print(f"\n🗑  Wiping analytics data for: {label}\n")

    total_deleted = 0
    for name, model in ANALYTICS_MODELS_WITH_APP_TYPE:
        if args.all:
            qs = model.objects.all()
        else:
            qs = model.objects.filter(appType=args.app_type)
        count = qs.count()
        if count > 0:
            qs.delete()
            print(f"  ✓ {name}: deleted {count} records")
        else:
            print(f"  - {name}: nothing to delete")
        total_deleted += count

    print(f"\nDone — {total_deleted} total records deleted.\n")


# ─── Export ──────────────────────────────────────────────────────────────────

def _safe_str(value):
    """Convert a value to a CSV-safe string."""
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return str(value)
    return str(value)


def _export_model(model, fields, csv_path):
    """Export a Django model queryset to a CSV file."""
    qs = model.objects.all()
    count = qs.count()

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for obj in qs:
            row = []
            for field in fields:
                val = getattr(obj, field, None)
                row.append(_safe_str(val))
            writer.writerow(row)

    return count


def _export_embedded(parent_model, parent_id_field, embedded_field, embedded_fields, csv_path):
    """Export embedded sub-documents as a separate CSV with a FK column."""
    qs = parent_model.objects.all()
    count = 0

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([parent_id_field] + embedded_fields)
        for parent in qs:
            parent_id = _safe_str(parent.id)
            items = getattr(parent, embedded_field, None) or []
            for item in items:
                row = [parent_id]
                for field in embedded_fields:
                    val = getattr(item, field, None)
                    row.append(_safe_str(val))
                writer.writerow(row)
                count += 1

    return count


# Collection registry: (key, display_name, model, fields)
EXPORT_REGISTRY = [
    (
        "users", "Users", User,
        ["id", "schema", "firebase_uid", "name", "email", "phone",
         "address", "profile_photo", "initials", "pets", "family_group",
         "created_at", "updated_at"],
    ),
    (
        "pets", "Pets", Pet,
        ["id", "schema", "name", "species", "breed", "gender",
         "birth_date", "weight", "color", "photo_url", "status",
         "is_nfc_synced", "known_allergies", "default_vet",
         "default_clinic", "owners"],
    ),
    (
        "vaccines", "Vaccines", Vaccine,
        ["id", "schema", "name", "species", "product_name",
         "manufacturer", "interval_days", "description"],
    ),
    (
        "events", "Events", Event,
        ["id", "schema", "pet_id", "owner_id", "title", "event_type",
         "date", "price", "provider", "clinic", "description",
         "follow_up_date"],
    ),
    (
        "notifications", "Notifications", Notification,
        ["id", "schema", "user_id", "type", "header", "text",
         "date_sent", "date_clicked", "is_read"],
    ),
    (
        "screens", "Screens", Screen,
        ["id", "schema", "name", "hasAds", "appType"],
    ),
    (
        "features", "Features", Feature,
        ["id", "schema", "name", "originButton", "originScreen", "appType"],
    ),
    (
        "feature_routes", "Feature Routes", FeatureRoute,
        ["id", "schema", "name", "originButton", "originScreen",
         "endButton", "endScreen", "appType"],
    ),
    (
        "screen_time_logs", "Screen Time Logs", ScreenTimeLog,
        ["id", "schema", "userId", "screenId", "startTime", "endTime",
         "totalTime", "appType"],
    ),
    (
        "feature_execution_logs", "Feature Execution Logs", FeatureExecutionLog,
        ["id", "schema", "userId", "featureId", "startTime", "endTime",
         "totalTime", "downloadSpeed", "uploadSpeed", "appType"],
    ),
    (
        "feature_clicks_logs", "Feature Clicks Logs", FeatureClicksLog,
        ["id", "schema", "userId", "routeId", "timestamp", "nClicks",
         "appType"],
    ),
]

# Embedded sub-document registries
EMBEDDED_EXPORTS = [
    (
        "screen_buttons", "Screen Buttons",
        Screen, "screen_id", "buttons",
        ["buttonId", "schema", "name"],
    ),
    (
        "pet_vaccinations", "Pet Vaccinations",
        Pet, "pet_id", "vaccinations",
        ["id", "vaccine_id", "date_given", "next_due_date", "lot_number",
         "status", "administered_by", "clinic_name"],
    ),
]


def cmd_export(args):
    """Export database collections to CSV files."""
    output_dir = args.output_dir or os.path.join(os.getcwd(), "exports")
    os.makedirs(output_dir, exist_ok=True)

    # Determine which collections to export
    requested = set(args.collections) if args.collections else None

    print(f"\n📤  Exporting to: {output_dir}\n")

    total_files = 0

    # Main collections
    for key, display, model, fields in EXPORT_REGISTRY:
        if requested and key not in requested:
            continue
        csv_path = os.path.join(output_dir, f"{key}.csv")
        count = _export_model(model, fields, csv_path)
        print(f"  ✓ {display}: {count} records → {key}.csv")
        total_files += 1

    # Embedded sub-documents
    for key, display, parent_model, parent_fk, embedded_field, embedded_fields in EMBEDDED_EXPORTS:
        parent_key = {Screen: "screens", Pet: "pets"}[parent_model]
        if requested and parent_key not in requested and key not in requested:
            continue
        csv_path = os.path.join(output_dir, f"{key}.csv")
        count = _export_embedded(
            parent_model, parent_fk, embedded_field, embedded_fields, csv_path
        )
        print(f"  ✓ {display}: {count} records → {key}.csv")
        total_files += 1

    print(f"\nDone — {total_files} CSV files exported to {output_dir}\n")


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="PetCare Analytics Database Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- wipe ---
    wipe_parser = subparsers.add_parser(
        "wipe",
        help="Delete analytics data (screens, features, routes, logs)",
    )
    wipe_group = wipe_parser.add_mutually_exclusive_group(required=True)
    wipe_group.add_argument(
        "--app-type",
        type=str,
        help="Only delete records with this appType (e.g. Kotlin, Flutter)",
    )
    wipe_group.add_argument(
        "--all",
        action="store_true",
        help="Delete ALL analytics data regardless of appType",
    )

    # --- export ---
    export_parser = subparsers.add_parser(
        "export",
        help="Export database collections to CSV for Power BI",
    )
    export_parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to write CSV files (default: ./exports)",
    )
    export_parser.add_argument(
        "--collections",
        nargs="+",
        type=str,
        default=None,
        help="Only export these collections (e.g. screens features users)",
    )

    args = parser.parse_args()

    if args.command == "wipe":
        cmd_wipe(args)
    elif args.command == "export":
        cmd_export(args)


if __name__ == "__main__":
    main()
