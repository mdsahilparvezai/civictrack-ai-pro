"""Sample/synthetic dataset for CivicTrack AI Pro.

IMPORTANT: All data in this module is synthetic and created for demonstration
and development purposes only. It is NOT verified official government data and
does not represent real civic infrastructure, complaints, projects, or budgets.
Do not present this data as official or authoritative.
"""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd


_CATEGORIES = [
    "Pothole",
    "Street Light",
    "Graffiti",
    "Trash Collection",
    "Water Main",
    "Park Maintenance",
    "Traffic Signal",
    "Sidewalk",
]

_STATUSES = ["Open", "In Progress", "Resolved", "Closed"]
_PRIORITIES = ["Low", "Medium", "High", "Critical"]
_LOCATIONS = [
    "Main St & 5th Ave",
    "Oak Street Park",
    "North 12th Avenue",
    "City Hall Plaza",
    "Riverfront Drive",
    "Maple & Elm Intersection",
    "Central Library Block",
    "Eastside Community Center",
    "West Ridge Road",
    "South Market Square",
]


def load_complaints() -> pd.DataFrame:
    """Return a sample DataFrame of civic complaints/issues.

    Columns:
        issue_id:    Sample ticket identifier.
        category:    Type of civic issue.
        location:    Where the issue was reported.
        priority:    Priority level (Low, Medium, High, Critical).
        status:      Current workflow status.
        date_reported: Date the issue was reported.
        description: Short sample description.
    """
    today = date.today()
    rows = [
        {
            "issue_id": "CT-1001",
            "category": "Pothole",
            "location": "Main St & 5th Ave",
            "priority": "High",
            "status": "Open",
            "date_reported": today - timedelta(days=2),
            "description": "Large pothole damaging vehicles near the intersection.",
        },
        {
            "issue_id": "CT-1002",
            "category": "Street Light",
            "location": "Oak Street Park",
            "priority": "Medium",
            "status": "In Progress",
            "date_reported": today - timedelta(days=5),
            "description": "Street lamp outage along the north walking path.",
        },
        {
            "issue_id": "CT-1003",
            "category": "Graffiti",
            "location": "City Hall Plaza",
            "priority": "Low",
            "status": "Resolved",
            "date_reported": today - timedelta(days=9),
            "description": "Graffiti removed from the west wall.",
        },
        {
            "issue_id": "CT-1004",
            "category": "Trash Collection",
            "location": "Eastside Community Center",
            "priority": "Medium",
            "status": "Open",
            "date_reported": today - timedelta(days=1),
            "description": "Missed trash pickup for two consecutive weeks.",
        },
        {
            "issue_id": "CT-1005",
            "category": "Water Main",
            "location": "Riverfront Drive",
            "priority": "Critical",
            "status": "Open",
            "date_reported": today - timedelta(days=3),
            "description": "Suspected water main leak causing low pressure.",
        },
        {
            "issue_id": "CT-1006",
            "category": "Park Maintenance",
            "location": "South Market Square",
            "priority": "Low",
            "status": "Closed",
            "date_reported": today - timedelta(days=14),
            "description": "Broken bench repaired and landscaping completed.",
        },
        {
            "issue_id": "CT-1007",
            "category": "Traffic Signal",
            "location": "Maple & Elm Intersection",
            "priority": "High",
            "status": "In Progress",
            "date_reported": today - timedelta(days=4),
            "description": "Pedestrian crossing signal not changing on request.",
        },
        {
            "issue_id": "CT-1008",
            "category": "Sidewalk",
            "location": "West Ridge Road",
            "priority": "Medium",
            "status": "Open",
            "date_reported": today - timedelta(days=6),
            "description": "Cracked sidewalk slab creating a trip hazard.",
        },
        {
            "issue_id": "CT-1009",
            "category": "Pothole",
            "location": "North 12th Avenue",
            "priority": "High",
            "status": "Resolved",
            "date_reported": today - timedelta(days=11),
            "description": "Pothole filled and road surface restored.",
        },
        {
            "issue_id": "CT-1010",
            "category": "Street Light",
            "location": "Central Library Block",
            "priority": "Low",
            "status": "Closed",
            "date_reported": today - timedelta(days=18),
            "description": "Faulty ballast replaced; lighting restored.",
        },
    ]
    return pd.DataFrame(rows)


def load_projects() -> pd.DataFrame:
    """Return a sample DataFrame of civic budget projects.

    Columns:
        project_id:   Sample project identifier.
        name:         Project name.
        category:     Project category.
        budget:       Total allocated budget (sample USD).
        spent:        Amount spent to date (sample USD).
        progress:     Completion percentage (0-100).
        status:       Project status (Active, On Hold, Completed).
        location:     Project location.
    """
    rows = [
        {
            "project_id": "PRJ-2001",
            "name": "Main Street Resurfacing",
            "category": "Transportation",
            "budget": 450000,
            "spent": 310000,
            "progress": 70,
            "status": "Active",
            "location": "Main St (1st to 10th)",
        },
        {
            "project_id": "PRJ-2002",
            "name": "LED Streetlight Upgrade",
            "category": "Utilities",
            "budget": 210000,
            "spent": 125000,
            "progress": 55,
            "status": "Active",
            "location": "Citywide residential zones",
        },
        {
            "project_id": "PRJ-2003",
            "name": "Riverfront Park Revitalization",
            "category": "Parks & Recreation",
            "budget": 320000,
            "spent": 320000,
            "progress": 100,
            "status": "Completed",
            "location": "Riverfront Drive",
        },
        {
            "project_id": "PRJ-2004",
            "name": "North District Water Main Replacement",
            "category": "Utilities",
            "budget": 680000,
            "spent": 150000,
            "progress": 25,
            "status": "Active",
            "location": "North 12th Avenue area",
        },
        {
            "project_id": "PRJ-2005",
            "name": "Downtown Sidewalk Repair Program",
            "category": "Transportation",
            "budget": 180000,
            "spent": 45000,
            "progress": 30,
            "status": "On Hold",
            "location": "Downtown core",
        },
        {
            "project_id": "PRJ-2006",
            "name": "Traffic Signal Modernization",
            "category": "Transportation",
            "budget": 260000,
            "spent": 210000,
            "progress": 85,
            "status": "Active",
            "location": "Major intersections",
        },
    ]
    return pd.DataFrame(rows)


def compute_kpi_metrics(complaints: pd.DataFrame, projects: pd.DataFrame) -> dict:
    """Compute dashboard KPI metrics from the provided datasets."""
    pending_statuses = {"Open", "In Progress"}

    total_complaints = int(len(complaints)) if complaints is not None else 0
    if complaints is not None and not complaints.empty and "status" in complaints.columns:
        pending_issues = int(
            complaints["status"].isin(pending_statuses).sum()
        )
        resolved_issues = int((complaints["status"] == "Resolved").sum())
    else:
        pending_issues = 0
        resolved_issues = 0

    active_projects = 0
    if projects is not None and not projects.empty and "status" in projects.columns:
        active_projects = int((projects["status"] == "Active").sum())

    return {
        "total_complaints": total_complaints,
        "pending_issues": pending_issues,
        "resolved_issues": resolved_issues,
        "active_projects": active_projects,
    }
