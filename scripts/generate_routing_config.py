"""
Generate routing_config.xlsx — maps teams to individual assignees and their emails.
Run once:  python scripts/generate_routing_config.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


ROUTING_DATA = [
    # Testing Team
    {"Team": "Testing Team", "Assignee": "Alice Tester", "Email": "alice.tester@company.com", "Role": "Lead QA", "Max_Tickets": 10},
    {"Team": "Testing Team", "Assignee": "Bob QA", "Email": "bob.qa@company.com", "Role": "QA Engineer", "Max_Tickets": 15},
    {"Team": "Testing Team", "Assignee": "Carol Test", "Email": "carol.test@company.com", "Role": "Automation Engineer", "Max_Tickets": 15},

    # EDI Team
    {"Team": "EDI Team", "Assignee": "Dan EDI", "Email": "dan.edi@company.com", "Role": "EDI Lead", "Max_Tickets": 10},
    {"Team": "EDI Team", "Assignee": "Eve Mapping", "Email": "eve.mapping@company.com", "Role": "EDI Analyst", "Max_Tickets": 15},
    {"Team": "EDI Team", "Assignee": "Frank Partner", "Email": "frank.partner@company.com", "Role": "Partner Integration", "Max_Tickets": 12},

    # BizTalk Team
    {"Team": "BizTalk Team", "Assignee": "Grace BT", "Email": "grace.bt@company.com", "Role": "BizTalk Lead", "Max_Tickets": 8},
    {"Team": "BizTalk Team", "Assignee": "Hank Orchestrator", "Email": "hank.orch@company.com", "Role": "BizTalk Developer", "Max_Tickets": 12},
    {"Team": "BizTalk Team", "Assignee": "Irene Pipeline", "Email": "irene.pipeline@company.com", "Role": "Integration Developer", "Max_Tickets": 12},

    # Database Team
    {"Team": "Database Team", "Assignee": "Jake DBA", "Email": "jake.dba@company.com", "Role": "Senior DBA", "Max_Tickets": 8},
    {"Team": "Database Team", "Assignee": "Karen SQL", "Email": "karen.sql@company.com", "Role": "Database Developer", "Max_Tickets": 12},
    {"Team": "Database Team", "Assignee": "Leo DB", "Email": "leo.db@company.com", "Role": "Database Analyst", "Max_Tickets": 12},

    # Network Team
    {"Team": "Network Team", "Assignee": "Mia Network", "Email": "mia.network@company.com", "Role": "Network Engineer", "Max_Tickets": 15},
    {"Team": "Network Team", "Assignee": "Ned Infra", "Email": "ned.infra@company.com", "Role": "Infrastructure Engineer", "Max_Tickets": 15},

    # Access Team
    {"Team": "Access Team", "Assignee": "Olivia IAM", "Email": "olivia.iam@company.com", "Role": "IAM Specialist", "Max_Tickets": 20},
    {"Team": "Access Team", "Assignee": "Pete AD", "Email": "pete.ad@company.com", "Role": "AD Administrator", "Max_Tickets": 20},

    # Security Team
    {"Team": "Security Team", "Assignee": "Quinn Sec", "Email": "quinn.sec@company.com", "Role": "Security Analyst", "Max_Tickets": 10},
    {"Team": "Security Team", "Assignee": "Rachel CISO", "Email": "rachel.ciso@company.com", "Role": "Security Lead", "Max_Tickets": 8},
]

# Team lead emails — used for auto-route notification emails
TEAM_LEAD_DATA = [
    {"Team": "Testing Team", "Lead_Name": "Alice Tester", "Lead_Email": "alice.tester@company.com"},
    {"Team": "EDI Team", "Lead_Name": "Dan EDI", "Lead_Email": "dan.edi@company.com"},
    {"Team": "BizTalk Team", "Lead_Name": "Grace BT", "Lead_Email": "grace.bt@company.com"},
    {"Team": "Database Team", "Lead_Name": "Jake DBA", "Lead_Email": "jake.dba@company.com"},
    {"Team": "Network Team", "Lead_Name": "Mia Network", "Lead_Email": "mia.network@company.com"},
    {"Team": "Access Team", "Lead_Name": "Olivia IAM", "Lead_Email": "olivia.iam@company.com"},
    {"Team": "Security Team", "Lead_Name": "Rachel CISO", "Lead_Email": "rachel.ciso@company.com"},
]


def main() -> None:
    out_dir = Path("data")
    out_dir.mkdir(exist_ok=True)

    path = out_dir / "routing_config.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame(ROUTING_DATA).to_excel(writer, index=False, sheet_name="Routing")
        pd.DataFrame(TEAM_LEAD_DATA).to_excel(writer, index=False, sheet_name="TeamLeads")

    print(f"✓ Routing config written → {path}")


if __name__ == "__main__":
    main()
