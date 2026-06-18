"""
Generate synthetic labeled ticket data (300+ rows) for training and testing.
Run once:  python scripts/generate_sample_data.py
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

random.seed(42)

# ── Team / category definitions ───────────────────────────────────────────────
TEAM_CATEGORIES: dict[str, list[str]] = {
    "Testing Team": [
        "Test case failure",
        "Regression test blocked",
        "UAT environment issue",
        "Automation script error",
        "Test data missing",
        "QA sign-off pending",
        "Performance test failure",
    ],
    "EDI Team": [
        "EDI transaction error",
        "835 file not received",
        "837 claim rejection",
        "EDI partner connectivity",
        "HIPAA validation failure",
        "EDI mapping issue",
        "Acknowledgement not received",
        "Trading partner setup",
    ],
    "BizTalk Team": [
        "BizTalk orchestration failure",
        "Message routing error",
        "BizTalk pipeline exception",
        "Suspended message in BizTalk",
        "BizTalk adapter configuration",
        "Schema validation error",
        "BizTalk host instance down",
        "Tracking database issue",
    ],
    "Database Team": [
        "Database connection timeout",
        "Slow query performance",
        "Deadlock detected",
        "Backup job failure",
        "Data integrity issue",
        "Stored procedure error",
        "Database migration failure",
        "Disk space alert on DB server",
        "Index rebuild needed",
        "Replication lag",
    ],
    "Network Team": [
        "VPN connectivity issue",
        "Network latency spike",
        "Firewall rule blocking traffic",
        "DNS resolution failure",
        "Load balancer misconfiguration",
    ],
    "Access Team": [
        "User account locked",
        "Password reset request",
        "Permission denied on folder",
        "MFA not working",
        "New user onboarding access",
    ],
    "Security Team": [
        "Suspicious login attempt",
        "Malware detected on endpoint",
        "Phishing email reported",
        "Security patch deployment",
        "Compliance audit finding",
    ],
}

PRIORITIES = {
    "P1": 0.10,
    "P2": 0.25,
    "P3": 0.45,
    "P4": 0.20,
}

STATUSES = ["Open", "In Progress", "Resolved", "Closed", "Pending"]

REPORTERS = [
    "John Smith", "Maria Garcia", "David Lee", "Sarah Johnson", "Michael Brown",
    "Emily Davis", "Robert Wilson", "Jessica Martinez", "William Anderson",
    "Linda Thomas", "James Jackson", "Barbara White", "Richard Harris",
    "Susan Clark", "Joseph Lewis",
]

TEAM_LEADS: dict[str, list[str]] = {
    "Testing Team": ["Alice Tester", "Bob QA", "Carol Test"],
    "EDI Team": ["Dan EDI", "Eve Mapping", "Frank Partner"],
    "BizTalk Team": ["Grace BT", "Hank Orchestrator", "Irene Pipeline"],
    "Database Team": ["Jake DBA", "Karen SQL", "Leo DB"],
    "Network Team": ["Mia Network", "Ned Infra"],
    "Access Team": ["Olivia IAM", "Pete AD"],
    "Security Team": ["Quinn Sec", "Rachel CISO"],
}

DESCRIPTION_TEMPLATES = [
    "User reported that {category} is causing disruption in production environment. Immediate attention required.",
    "Multiple users are affected by {category}. Business impact is {impact}. Please investigate and resolve.",
    "{category} was detected at {time}. The system logs indicate an error in the processing layer.",
    "Ticket raised for {category}. Initial triage suggests it may be related to recent deployment.",
    "Escalated issue: {category}. SLA breach imminent. Team lead notified.",
    "Automated monitoring triggered alert for {category}. No manual workaround available.",
    "End user submitted request regarding {category}. Priority set based on business impact.",
    "Recurrence of previous issue: {category}. Root cause analysis required after resolution.",
]

IMPACTS = ["high", "medium", "low", "critical"]

RESOLUTIONS = [
    "Root cause identified and fix deployed.",
    "Configuration updated. Monitoring for 24 hours.",
    "Escalated to vendor for further investigation.",
    "Temporary workaround applied. Permanent fix scheduled.",
    "Issue resolved after system restart.",
    "User training provided. Issue marked resolved.",
    "Patch applied and verified in staging before production push.",
    "",
]


def random_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


def build_row(ticket_id: int) -> dict:
    team = random.choices(
        list(TEAM_CATEGORIES.keys()),
        weights=[len(v) for v in TEAM_CATEGORIES.values()],
    )[0]
    category = random.choice(TEAM_CATEGORIES[team])
    priority = random.choices(list(PRIORITIES.keys()), weights=list(PRIORITIES.values()))[0]

    created = random_date(datetime(2024, 1, 1), datetime(2025, 12, 31))
    status = random.choice(STATUSES)
    resolution_hours = None
    resolution = ""
    if status in ("Resolved", "Closed"):
        resolution_hours = round(
            random.uniform(0.5, 72) if priority == "P1"
            else random.uniform(1, 120) if priority == "P2"
            else random.uniform(2, 240),
            1,
        )
        resolution = random.choice([r for r in RESOLUTIONS if r])

    assignee = random.choice(TEAM_LEADS[team])
    template = random.choice(DESCRIPTION_TEMPLATES)
    description = template.format(
        category=category,
        impact=random.choice(IMPACTS),
        time=created.strftime("%Y-%m-%d %H:%M"),
    )

    return {
        "Ticket_ID": f"TKT-{ticket_id:05d}",
        "Date": created.strftime("%Y-%m-%d %H:%M"),
        "Summary": category,
        "Description": description,
        "Reporter": random.choice(REPORTERS),
        "Category": category,
        "Priority": priority,
        "Assigned_Team": team,
        "Assigned_To": assignee,
        "Status": status,
        "Resolution": resolution,
        "Resolution_Time_Hours": resolution_hours,
    }


def main() -> None:
    out_dir = Path("data")
    out_dir.mkdir(exist_ok=True)

    rows = [build_row(i) for i in range(1, 51)]
    df = pd.DataFrame(rows)

    path = out_dir / "sample_tickets.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Tickets")

    print(f"✓ Generated {len(df)} tickets → {path}")
    print(f"  Team distribution:\n{df['Assigned_Team'].value_counts().to_string()}")
    print(f"  Priority distribution:\n{df['Priority'].value_counts().sort_index().to_string()}")


if __name__ == "__main__":
    main()
