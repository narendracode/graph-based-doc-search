#!/usr/bin/env python3
"""Generates synthetic NBCC-style PDFs for demo/testing (bulk upload, search, KG).

Each entry becomes one PDF in sample_data/, converted from Markdown via pandoc+pdflatex.
Filenames encode doc type + project so it's easy to pick consistent batches for
bulk-upload testing in the UI (a batch shares one doc_type/zone/project selection).

Usage: python3 scripts/generate_sample_docs.py
"""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "sample_data"

DOCS = [
    dict(
        filename="approval_delhi_metro_environmental_clearance",
        title="Environmental Clearance Approval",
        body="""
This approval is granted by the **Ministry of Environment, Forest and Climate Change**
for the **Delhi Metro Extension** project, Northern Zone.

- Approval Reference: NBCC/DME/ENV/2026/011
- Applicant: NBCC India Limited
- Contractor of Record: Larsen & Toubro Construction
- Zone: Northern Zone
- Date of Approval: 04 February 2026
- Validity: 5 years from date of issue

## Conditions

The environmental clearance is subject to compliance with dust control, noise
mitigation, and groundwater protection measures during the tunnelling phase between
Kashmere Gate and Red Fort stations.

## Remarks

No objections were raised by the State Pollution Control Board. This clearance
supersedes the provisional approval dated 12 September 2025.
""",
    ),
    dict(
        filename="approval_chennai_housing_layout",
        title="Layout Plan Approval",
        body="""
Layout plan approval for the **Chennai Housing Board** residential project, Southern
Zone.

- Approval Reference: NBCC/CHB/LAYOUT/2026/004
- Applicant: NBCC India Limited
- Approving Authority: Chennai Metropolitan Development Authority
- Zone: Southern Zone
- Date of Approval: 18 January 2026

## Details

The approved layout covers 42 acres comprising 6 residential towers, a community
center, and allocated green space of 18% of total plot area, in line with CMDA
building regulations 2024.
""",
    ),
    dict(
        filename="approval_mumbai_coastal_cost_revision",
        title="Cost Revision Approval",
        body="""
Approval for revised project cost for the **Mumbai Coastal Road** project, Western
Zone.

- Approval Reference: NBCC/MCR/COST/2026/009
- Original Sanctioned Cost: Rs 145,00,00,000
- Revised Sanctioned Cost: Rs 168,50,00,000
- Reason: Increase in steel and cement input costs, additional dredging scope
- Approved By: NBCC Board of Directors
- Date of Approval: 27 February 2026
- Contractor: Afcons Infrastructure Ltd
""",
    ),
    dict(
        filename="contract_delhi_metro_civil_works",
        title="Civil Works Contract",
        body="""
This contract is entered into between **NBCC India Limited** and **Larsen & Toubro
Construction** for civil works on the **Delhi Metro Extension** project.

- Contract Reference: NBCC/DME/2026/0042
- Contract Value: Rs 50,00,00,000
- Date of Signing: 15 January 2026
- Zone: Northern Zone

## Scope of Work

The contractor shall execute foundation work, structural steel erection, and
finishing work for the elevated corridor between Kashmere Gate and Red Fort stations,
as per the approved project plan NBCC/DME/PLAN/2026/002.

## Payment Terms

Payment shall be released in four milestones of Rs 12,50,00,000 each, subject to
inspection and certification by the NBCC project engineer, Northern Zone.
""",
    ),
    dict(
        filename="contract_chennai_housing_electrical",
        title="Electrical Works Contract",
        body="""
This contract is entered into between **NBCC India Limited** and **KEC International
Limited** for electrical installation works on the **Chennai Housing Board** project.

- Contract Reference: NBCC/CHB/2026/0018
- Contract Value: Rs 8,75,00,000
- Date of Signing: 22 January 2026
- Zone: Southern Zone

## Scope of Work

Supply and installation of internal wiring, transformers, and substation equipment
across all 6 residential towers, in accordance with layout approval
NBCC/CHB/LAYOUT/2026/004.
""",
    ),
    dict(
        filename="contract_mumbai_coastal_dredging",
        title="Dredging Works Contract",
        body="""
This contract is entered into between **NBCC India Limited** and **Afcons
Infrastructure Ltd** for dredging works on the **Mumbai Coastal Road** project.

- Contract Reference: NBCC/MCR/2026/0007
- Contract Value: Rs 22,40,00,000
- Date of Signing: 03 March 2026
- Zone: Western Zone

## Scope of Work

Dredging and reclamation work along the Worli-Haji Ali stretch, including disposal
of dredged material at the designated offshore site, per cost revision approval
NBCC/MCR/COST/2026/009.
""",
    ),
    dict(
        filename="contract_bengaluru_it_park_hvac",
        title="HVAC Installation Contract",
        body="""
This contract is entered into between **NBCC India Limited** and **Blue Star
Limited** for HVAC installation on the **Bengaluru IT Park** project.

- Contract Reference: NBCC/BIP/2026/0031
- Contract Value: Rs 6,20,00,000
- Date of Signing: 10 March 2026
- Zone: Southern Zone

## Scope of Work

Design, supply, and installation of centralized HVAC systems across Block A and
Block B of the IT park, as per project plan NBCC/BIP/PLAN/2026/001.
""",
    ),
    dict(
        filename="project_plan_delhi_metro_phase2",
        title="Phase 2 Project Plan",
        body="""
Project plan for Phase 2 of the **Delhi Metro Extension**, Northern Zone.

- Plan Reference: NBCC/DME/PLAN/2026/002
- Project Lead: NBCC India Limited
- Executing Contractor: Larsen & Toubro Construction
- Zone: Northern Zone
- Planned Start: 01 April 2026
- Planned Completion: 30 September 2028

## Milestones

1. Foundation and piling — Q2 2026
2. Elevated corridor structural work — Q4 2026 to Q3 2027
3. Track laying and signaling — Q4 2027
4. Trial runs and commissioning — Q2 2028

## Budget

Total estimated project cost: Rs 210,00,00,000, funded jointly by the Ministry of
Housing and Urban Affairs and the Delhi Metro Rail Corporation.
""",
    ),
    dict(
        filename="project_plan_bengaluru_it_park",
        title="Project Plan",
        body="""
Project plan for the **Bengaluru IT Park** development, Southern Zone.

- Plan Reference: NBCC/BIP/PLAN/2026/001
- Project Lead: NBCC India Limited
- Zone: Southern Zone
- Planned Start: 15 February 2026
- Planned Completion: 31 December 2027

## Scope

Construction of two office towers (Block A and Block B), a central plaza, and
underground parking for 800 vehicles, to be leased to IT and ITES occupants.

## Key Contractors

- Civil works: Shapoorji Pallonji and Company
- HVAC: Blue Star Limited (contract NBCC/BIP/2026/0031)
""",
    ),
    dict(
        filename="invoice_delhi_metro_milestone1",
        title="Milestone Invoice",
        body="""
Invoice raised by **Larsen & Toubro Construction** against **NBCC India Limited**
for the **Delhi Metro Extension** project.

- Invoice Reference: NBCC/DME/INV/2026/101
- Against Contract: NBCC/DME/2026/0042
- Milestone: 1 of 4 — Foundation work completion
- Invoice Amount: Rs 12,50,00,000
- Date of Invoice: 20 February 2026
- Zone: Northern Zone

Certified for payment by the NBCC project engineer, Northern Zone, following site
inspection on 18 February 2026.
""",
    ),
    dict(
        filename="invoice_chennai_housing_milestone2",
        title="Milestone Invoice",
        body="""
Invoice raised by **KEC International Limited** against **NBCC India Limited**
for the **Chennai Housing Board** project.

- Invoice Reference: NBCC/CHB/INV/2026/044
- Against Contract: NBCC/CHB/2026/0018
- Milestone: 2 of 3 — Substation equipment installation
- Invoice Amount: Rs 3,00,00,000
- Date of Invoice: 05 March 2026
- Zone: Southern Zone
""",
    ),
    dict(
        filename="invoice_mumbai_coastal_milestone1",
        title="Milestone Invoice",
        body="""
Invoice raised by **Afcons Infrastructure Ltd** against **NBCC India Limited**
for the **Mumbai Coastal Road** project.

- Invoice Reference: NBCC/MCR/INV/2026/012
- Against Contract: NBCC/MCR/2026/0007
- Milestone: 1 of 3 — Mobilization and initial dredging
- Invoice Amount: Rs 6,00,00,000
- Date of Invoice: 25 March 2026
- Zone: Western Zone
""",
    ),
    dict(
        filename="agreement_delhi_metro_jv",
        title="Joint Venture Agreement",
        body="""
Joint venture agreement between **NBCC India Limited** and **Delhi Metro Rail
Corporation** for co-funding the **Delhi Metro Extension** project.

- Agreement Reference: NBCC/DME/JV/2026/001
- Parties: NBCC India Limited, Delhi Metro Rail Corporation
- Effective Date: 01 January 2026
- Zone: Northern Zone

## Terms

Funding shall be shared in a 60:40 ratio between the Ministry of Housing and Urban
Affairs (via NBCC) and the Delhi Metro Rail Corporation. Revenue from station-area
commercial leasing shall be split in the same ratio for a period of 15 years.
""",
    ),
    dict(
        filename="agreement_bengaluru_it_park_lease",
        title="Master Lease Agreement",
        body="""
Master lease agreement between **NBCC India Limited** and **Global Tech Park
Occupiers Association** for the **Bengaluru IT Park**.

- Agreement Reference: NBCC/BIP/LEASE/2026/002
- Parties: NBCC India Limited, Global Tech Park Occupiers Association
- Zone: Southern Zone
- Lease Term: 10 years, renewable
- Effective Date: 01 January 2028 (on project completion)

## Terms

Lease rent shall be revised every 3 years in line with prevailing commercial rates
in the Whitefield micro-market, subject to a floor escalation of 5% per revision.
""",
    ),
    dict(
        filename="other_delhi_metro_site_survey_report",
        title="Site Survey Report",
        body="""
Site survey report for the **Delhi Metro Extension** project, Northern Zone.

- Report Reference: NBCC/DME/SURVEY/2026/003
- Prepared By: NBCC India Limited, Northern Zone Engineering Cell
- Date: 10 January 2026

## Findings

Topographical survey between Kashmere Gate and Red Fort stations identified two
utility corridors (water and telecom) requiring diversion before piling work can
commence. Recommended diversion cost: Rs 1,20,00,000, to be incorporated into the
Phase 2 project plan (NBCC/DME/PLAN/2026/002).
""",
    ),
    dict(
        filename="other_chennai_housing_soil_test_report",
        title="Soil Test Report",
        body="""
Geotechnical soil test report for the **Chennai Housing Board** project, Southern
Zone.

- Report Reference: NBCC/CHB/SOIL/2026/002
- Prepared By: Geotech Consultants Pvt Ltd, on behalf of NBCC India Limited
- Date: 05 December 2025

## Findings

Soil bearing capacity across the 42-acre site ranges from 12 to 18 tonnes per square
metre, adequate for the raft foundation design proposed for all 6 residential
towers under layout approval NBCC/CHB/LAYOUT/2026/004.
""",
    ),
]


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    for doc in DOCS:
        md_path = OUT_DIR / f"{doc['filename']}.md"
        pdf_path = OUT_DIR / f"{doc['filename']}.pdf"
        md_path.write_text(f"# {doc['title']}\n{doc['body']}")
        subprocess.run(
            [
                "pandoc",
                str(md_path),
                "-o",
                str(pdf_path),
                "--pdf-engine=pdflatex",
                "-V",
                "pagestyle=empty",  # no page-number footer leaking into parsed chunks
            ],
            check=True,
            cwd=OUT_DIR,
        )
        md_path.unlink()
        print(f"generated {pdf_path.name}")
    print(f"\n{len(DOCS)} sample PDFs written to {OUT_DIR}")


if __name__ == "__main__":
    main()
