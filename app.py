import gradio as gr

# ============================================================================
# OpenLine Readiness Simulator
# Phase 4A: Readiness Scoring Engine
# ============================================================================
#
# WHY THIS CODE IS STRUCTURED THE WAY IT IS:
#
# Every assumption in this simulator is defensible against published research.
# The four sub-score weightings reflect mainstream pharma operations literature
# (McKinsey, Deloitte, ISPE) which consistently identifies organizational and
# process risks as the dominant causes of digital transformation failure,
# ranking ahead of technical risks. Catalyx's own 2025 Line Clearance
# Benchmark Report reinforces this: their finding that "pilots fail to scale"
# is fundamentally an organizational/process problem, not a technical one.
#
# Each input is mapped to a 0-100 sub-score via a lookup table. The tables
# are kept visible at the top of this file so any reader (or interviewer)
# can audit the assumptions.
#
# ============================================================================


# ============================================================================
# SCORING TABLES — every assumption is here, visible and auditable
# ============================================================================

# --- Sub-score weightings (must sum to 1.0) ---
WEIGHTS = {
    "process":        0.30,  # how mature is the existing line clearance process
    "organizational": 0.30,  # workforce readiness + change-management history
    "regulatory":     0.25,  # inspection posture + validation maturity
    "technical":      0.15,  # IT/OT integration burden
}

# --- Process readiness inputs ---
SCORE_CURRENT_METHOD = {
    "Fully paper-based":             10,
    "Hybrid (some digital, some paper)": 40,
    "Partially digitized":           70,
    "Mostly digital":                95,
}

SCORE_CLEARANCE_DURATION = {
    "Under 30 minutes":  90,
    "30–60 minutes":     70,
    "1–2 hours":         45,
    "Over 2 hours":      20,
}

SCORE_DEVIATION_FREQUENCY = {
    "None":       100,
    "1–2":         75,
    "3–5":         45,
    "6 or more":   15,
}

# --- Organizational readiness inputs ---
SCORE_OPERATOR_FAMILIARITY = {
    "High":   90,
    "Medium": 60,
    "Low":    25,
}

# Past-attempt history is the single most predictive question in the model.
# A previously failed attempt creates organizational scar tissue that
# significantly reduces the probability of a future rollout succeeding.
SCORE_PRIOR_ATTEMPT = {
    "Yes — successful":         95,
    "No — first attempt":       60,
    "Yes — stalled or failed":  25,
}

# --- Regulatory readiness inputs ---
SCORE_INSPECTION_OUTCOME = {
    "Clean (no observations)":             95,
    "Minor observations":                  70,
    "Major observations":                  25,
    "Not applicable / never inspected":    55,  # neutral — no signal either way
}

SCORE_VALIDATION_MATURITY = {
    "Mature (templates, dedicated team)": 95,
    "Functional but ad-hoc":              55,
    "Underdeveloped":                     20,
}

# --- Technical readiness inputs ---
# Modern, well-known MES systems integrate cleanly. Custom or absent
# systems create much higher integration burden.
SCORE_MES_SYSTEM = {
    "SAP":           80,
    "Werum PAS-X":   90,  # pharma-purpose-built, easiest integration
    "Rockwell":      75,
    "Tulip":         70,
    "Other / Custom": 40,
    "None":          25,  # no MES = significant integration work needed
}

SCORE_EBR_SYSTEM = {
    "Yes":     90,
    "Partial": 55,
    "No":      25,
}

SCORE_EQUIPMENT_AGE = {
    "Mostly under 5 years":          90,
    "Mixed (some new, some old)":    60,
    "Mostly over 10 years":          30,
}


# --- Verdict bands ---
# Tightened cutoffs vs. naive even thirds to prevent false "green light"
# verdicts for middling factories. A top-band score should be earned.
VERDICT_BANDS = [
    (80, 100, "Ready to scale",
     "Proceed with full rollout planning. Risks are manageable; ROI is defensible."),
    (65, 79, "Ready with caveats",
     "Address the flagged risks before committing to a full rollout. "
     "Most readiness gaps are closeable in 1–3 months."),
    (45, 64, "Not yet ready",
     "Significant gaps to close first. A premature rollout is likely to stall. "
     "Focus on the lowest-scoring sub-category before reassessing."),
    (0, 44, "High risk",
     "Recommend additional limited pilot scope rather than a full rollout. "
     "Foundational gaps in process, organization, or regulation need attention first."),
]


# ============================================================================
# SCORING ENGINE
# ============================================================================

def compute_readiness_score(
    # Section 1 (unused in scoring — used for ROI in Phase 4B)
    num_lines, num_facilities, annual_volume, product_type,
    # Section 2
    current_method, clearance_duration, changeovers_per_week, deviation_frequency,
    # Section 3
    mes_system, ebr_system, equipment_age,
    # Section 4
    inspection_outcome, validation_maturity,
    # Section 5
    operator_familiarity, prior_attempt,
):
    """
    Compute the four sub-scores and the weighted total readiness score.

    Returns a dictionary with all the numbers and explanation strings,
    so the UI layer can format them however it wants.
    """

    # --- Process readiness (avg of 3 inputs) ---
    process_inputs = [
        SCORE_CURRENT_METHOD[current_method],
        SCORE_CLEARANCE_DURATION[clearance_duration],
        SCORE_DEVIATION_FREQUENCY[deviation_frequency],
    ]
    process_score = sum(process_inputs) / len(process_inputs)

    # --- Organizational readiness (avg of 2 inputs) ---
    org_inputs = [
        SCORE_OPERATOR_FAMILIARITY[operator_familiarity],
        SCORE_PRIOR_ATTEMPT[prior_attempt],
    ]
    org_score = sum(org_inputs) / len(org_inputs)

    # --- Regulatory readiness (avg of 2 inputs) ---
    reg_inputs = [
        SCORE_INSPECTION_OUTCOME[inspection_outcome],
        SCORE_VALIDATION_MATURITY[validation_maturity],
    ]
    reg_score = sum(reg_inputs) / len(reg_inputs)

    # --- Technical readiness (avg of 3 inputs) ---
    tech_inputs = [
        SCORE_MES_SYSTEM[mes_system],
        SCORE_EBR_SYSTEM[ebr_system],
        SCORE_EQUIPMENT_AGE[equipment_age],
    ]
    tech_score = sum(tech_inputs) / len(tech_inputs)

    # --- Weighted total ---
    total = (
        process_score * WEIGHTS["process"]
        + org_score * WEIGHTS["organizational"]
        + reg_score * WEIGHTS["regulatory"]
        + tech_score * WEIGHTS["technical"]
    )

    # --- Verdict band ---
    verdict_label = ""
    verdict_message = ""
    for low, high, label, message in VERDICT_BANDS:
        if low <= total <= high:
            verdict_label = label
            verdict_message = message
            break

    return {
        "total":           round(total, 1),
        "process":         round(process_score, 1),
        "organizational":  round(org_score, 1),
        "regulatory":      round(reg_score, 1),
        "technical":       round(tech_score, 1),
        "verdict_label":   verdict_label,
        "verdict_message": verdict_message,
    }


# ============================================================================
# UI HANDLER — turns the score dict into a Markdown summary
# ============================================================================

def process_form(
    num_lines, num_facilities, annual_volume, product_type,
    current_method, clearance_duration, changeovers_per_week, deviation_frequency,
    mes_system, ebr_system, equipment_age,
    inspection_outcome, validation_maturity,
    operator_familiarity, prior_attempt,
):
    result = compute_readiness_score(
        num_lines, num_facilities, annual_volume, product_type,
        current_method, clearance_duration, changeovers_per_week, deviation_frequency,
        mes_system, ebr_system, equipment_age,
        inspection_outcome, validation_maturity,
        operator_familiarity, prior_attempt,
    )

    summary = f"""
## Readiness Assessment

### Overall Readiness Score: **{result['total']} / 100**

### Verdict: **{result['verdict_label']}**
{result['verdict_message']}

---

### Sub-score Breakdown

| Category | Weight | Score |
|---|---|---|
| Process readiness | 30% | **{result['process']}** / 100 |
| Organizational readiness | 30% | **{result['organizational']}** / 100 |
| Regulatory readiness | 25% | **{result['regulatory']}** / 100 |
| Technical readiness | 15% | **{result['technical']}** / 100 |

---

### What's driving this score

**Process readiness ({result['process']}/100)** reflects your current line
clearance method ({current_method}), typical clearance duration
({clearance_duration}), and recent deviation history
({deviation_frequency} in the past 12 months).

**Organizational readiness ({result['organizational']}/100)** reflects your
operators' digital tool familiarity ({operator_familiarity}) and your
facility's history with line clearance digitization ({prior_attempt}).
*Past-attempt history is the single most predictive input in the model.*

**Regulatory readiness ({result['regulatory']}/100)** reflects your last
regulatory inspection outcome ({inspection_outcome}) and your computer
system validation maturity ({validation_maturity}).

**Technical readiness ({result['technical']}/100)** reflects your existing
MES ({mes_system}), eBR coverage ({ebr_system}), and equipment age
({equipment_age}). Technical readiness is weighted lowest (15%) because
published pharma operations research consistently identifies organizational
and process risks as the dominant causes of digital rollout failure.

---

*Coming next: ROI projection (Phase 4B), risk heatmap (Phase 4C),
and tailored next-steps recommendations (Phase 4D).*
"""
    return summary


# ============================================================================
# UI — exactly the same form as Phase 3B
# ============================================================================

INTRO_TEXT = """
# OpenLine Readiness Simulator

A free assessment tool that helps pharma manufacturing leaders evaluate whether
their factories are ready to roll out AI-powered line clearance — *before*
committing budget to a full deployment.

**Why this exists:**
Catalyx's own 2025 Line Clearance Benchmark Report shows that roughly half the
pharma industry piloted digital line clearance tools in 2023, but by 2025 only
**11% had actually rolled them out**. Most pilots succeed technically — and
then stall before becoming production deployments.

*Currently in development. This is Phase 4A — readiness scoring. ROI math,
risk heatmap, visual charts, and PDF export are coming in later phases.*

---

### Instructions
Answer the 15 questions below across 5 sections. All fields have sensible
defaults — adjust the ones that apply to your situation. Click **Submit** at
the bottom to see your readiness assessment.
"""

with gr.Blocks(
    title="OpenLine Readiness Simulator",
    theme=gr.themes.Soft(),
) as demo:

    gr.Markdown(INTRO_TEXT)

    with gr.Accordion("Section 1: Factory Profile", open=True):
        num_lines = gr.Slider(
            label="Number of production lines in scope for rollout",
            minimum=1, maximum=100, value=10, step=1,
        )
        num_facilities = gr.Slider(
            label="Number of facilities involved",
            minimum=1, maximum=20, value=2, step=1,
        )
        annual_volume = gr.Radio(
            label="Approximate annual production volume",
            choices=[
                "Under 1 million units",
                "1–10 million units",
                "10–100 million units",
                "Over 100 million units",
            ],
            value="1–10 million units",
        )
        product_type = gr.Radio(
            label="Primary product type",
            choices=["Oral solid dose", "Injectable", "Biologic", "Medical device", "Other"],
            value="Oral solid dose",
        )

    with gr.Accordion("Section 2: Current Line Clearance Practice", open=True):
        current_method = gr.Radio(
            label="Current line clearance method",
            choices=list(SCORE_CURRENT_METHOD.keys()),
            value="Hybrid (some digital, some paper)",
        )
        clearance_duration = gr.Radio(
            label="Average line clearance duration today",
            choices=list(SCORE_CLEARANCE_DURATION.keys()),
            value="1–2 hours",
        )
        changeovers_per_week = gr.Slider(
            label="Average number of changeovers per line per week",
            minimum=1, maximum=30, value=5, step=1,
        )
        deviation_frequency = gr.Radio(
            label="Line clearance deviations in the past 12 months",
            choices=list(SCORE_DEVIATION_FREQUENCY.keys()),
            value="3–5",
        )

    with gr.Accordion("Section 3: IT and Integration Landscape", open=True):
        mes_system = gr.Radio(
            label="Existing Manufacturing Execution System (MES)",
            choices=list(SCORE_MES_SYSTEM.keys()),
            value="None",
        )
        ebr_system = gr.Radio(
            label="Electronic batch record (eBR) system in place",
            choices=list(SCORE_EBR_SYSTEM.keys()),
            value="Partial",
        )
        equipment_age = gr.Radio(
            label="Equipment and PLC age",
            choices=list(SCORE_EQUIPMENT_AGE.keys()),
            value="Mixed (some new, some old)",
        )

    with gr.Accordion("Section 4: Regulatory and Quality Context", open=True):
        inspection_outcome = gr.Radio(
            label="Last regulatory inspection outcome",
            choices=list(SCORE_INSPECTION_OUTCOME.keys()),
            value="Minor observations",
        )
        validation_maturity = gr.Radio(
            label="Computer system validation maturity",
            choices=list(SCORE_VALIDATION_MATURITY.keys()),
            value="Functional but ad-hoc",
        )

    with gr.Accordion("Section 5: Workforce and Change-Management Context", open=True):
        operator_familiarity = gr.Radio(
            label="Operator digital tool familiarity",
            choices=list(SCORE_OPERATOR_FAMILIARITY.keys()),
            value="Medium",
        )
        prior_attempt = gr.Radio(
            label="Has your facility ever attempted a line clearance digitization project before?",
            choices=list(SCORE_PRIOR_ATTEMPT.keys()),
            value="No — first attempt",
        )

    submit_btn = gr.Button("Submit", variant="primary", size="lg")
    output = gr.Markdown()

    submit_btn.click(
        fn=process_form,
        inputs=[
            num_lines, num_facilities, annual_volume, product_type,
            current_method, clearance_duration, changeovers_per_week, deviation_frequency,
            mes_system, ebr_system, equipment_age,
            inspection_outcome, validation_maturity,
            operator_familiarity, prior_attempt,
        ],
        outputs=output,
    )


if __name__ == "__main__":
    demo.launch()