import gradio as gr

# ============================================================================
# OpenLine Readiness Simulator
# Phase 4B: Readiness Scoring + ROI Projection
# ============================================================================
#
# Every assumption in this simulator is sourced and visible at the top of
# this file. Readiness weightings follow mainstream pharma operations
# literature (McKinsey, Deloitte, ISPE), which identifies organizational and
# process risks as dominant failure modes ahead of technical risks. Catalyx's
# own 2025 Line Clearance Benchmark Report reinforces this. ROI assumptions
# use conservative midpoints of publicly available industry ranges; the user
# can override them in the Advanced section.
#
# ============================================================================


# ============================================================================
# READINESS SCORING TABLES (unchanged from Phase 4A)
# ============================================================================

WEIGHTS = {
    "process":        0.30,
    "organizational": 0.30,
    "regulatory":     0.25,
    "technical":      0.15,
}

SCORE_CURRENT_METHOD = {
    "Fully paper-based":                 10,
    "Hybrid (some digital, some paper)": 40,
    "Partially digitized":               70,
    "Mostly digital":                    95,
}

SCORE_CLEARANCE_DURATION = {
    "Under 30 minutes":  90,
    "30–60 minutes":     70,
    "1–2 hours":         45,
    "Over 2 hours":      20,
}

SCORE_DEVIATION_FREQUENCY = {
    "None":      100,
    "1–2":        75,
    "3–5":        45,
    "6 or more":  15,
}

SCORE_OPERATOR_FAMILIARITY = {
    "High":   90,
    "Medium": 60,
    "Low":    25,
}

SCORE_PRIOR_ATTEMPT = {
    "Yes — successful":        95,
    "No — first attempt":      60,
    "Yes — stalled or failed": 25,
}

SCORE_INSPECTION_OUTCOME = {
    "Clean (no observations)":          95,
    "Minor observations":               70,
    "Major observations":               25,
    "Not applicable / never inspected": 55,
}

SCORE_VALIDATION_MATURITY = {
    "Mature (templates, dedicated team)": 95,
    "Functional but ad-hoc":              55,
    "Underdeveloped":                     20,
}

SCORE_MES_SYSTEM = {
    "SAP":            80,
    "Werum PAS-X":    90,
    "Rockwell":       75,
    "Tulip":          70,
    "Other / Custom": 40,
    "None":           25,
}

SCORE_EBR_SYSTEM = {
    "Yes":     90,
    "Partial": 55,
    "No":      25,
}

SCORE_EQUIPMENT_AGE = {
    "Mostly under 5 years":       90,
    "Mixed (some new, some old)": 60,
    "Mostly over 10 years":       30,
}

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
# ROI ASSUMPTIONS — every default is visible and sourced
# ============================================================================

# Labor cost — fully-loaded operator hourly rate, US baseline.
# US Bureau of Labor Statistics pharma operator base wages run $25-30/hr.
# Fully-loaded (benefits, overhead, supervision, indirect) typically 2.0-2.5x,
# putting full cost at ~$50-75/hr. Midpoint = $65. EU runs higher,
# emerging markets lower. User can override in Advanced section.
DEFAULT_LABOR_RATE_USD_PER_HOUR = 65

# Time savings from OpenLine deployment.
# Catalyx markets 85% faster line clearance. We default to ~half of vendor
# claim (45%) because (a) vendor claims are aspirational, (b) real-world
# deployments capture only a fraction of demo-condition gains, (c) a
# defensible business case is built on conservative assumptions.
DEFAULT_TIME_SAVINGS_PCT = 45

# Per-line deployment cost.
# Industry rule-of-thumb for enterprise machine vision in pharma:
# $50k-150k per line depending on complexity. Our defaults sit mid-range
# and assume typical bulk-discount pattern.
DEFAULT_FIRST_LINE_COST_USD = 90_000
DEFAULT_ADDITIONAL_LINE_COST_USD = 55_000

# Operational defaults
NUM_OPERATORS_PER_CLEARANCE = 2  # Standard GMP: operator + QA witness
WEEKS_PER_YEAR = 48              # Standard pharma assumption (factoring shutdowns)

# Duration band → midpoint hours.
# Midpoints of each band; "Over 2 hours" anchored at 2.5h (many real
# clearances over 2h run 3-4h, so 2.5 is conservatively low).
DURATION_TO_HOURS = {
    "Under 30 minutes": 0.4,
    "30–60 minutes":    0.75,
    "1–2 hours":        1.5,
    "Over 2 hours":     2.5,
}


# ============================================================================
# SCORING ENGINE (unchanged from Phase 4A)
# ============================================================================

def compute_readiness_score(
    current_method, clearance_duration, deviation_frequency,
    operator_familiarity, prior_attempt,
    inspection_outcome, validation_maturity,
    mes_system, ebr_system, equipment_age,
):
    process_inputs = [
        SCORE_CURRENT_METHOD[current_method],
        SCORE_CLEARANCE_DURATION[clearance_duration],
        SCORE_DEVIATION_FREQUENCY[deviation_frequency],
    ]
    process_score = sum(process_inputs) / len(process_inputs)

    org_inputs = [
        SCORE_OPERATOR_FAMILIARITY[operator_familiarity],
        SCORE_PRIOR_ATTEMPT[prior_attempt],
    ]
    org_score = sum(org_inputs) / len(org_inputs)

    reg_inputs = [
        SCORE_INSPECTION_OUTCOME[inspection_outcome],
        SCORE_VALIDATION_MATURITY[validation_maturity],
    ]
    reg_score = sum(reg_inputs) / len(reg_inputs)

    tech_inputs = [
        SCORE_MES_SYSTEM[mes_system],
        SCORE_EBR_SYSTEM[ebr_system],
        SCORE_EQUIPMENT_AGE[equipment_age],
    ]
    tech_score = sum(tech_inputs) / len(tech_inputs)

    total = (
        process_score * WEIGHTS["process"]
        + org_score * WEIGHTS["organizational"]
        + reg_score * WEIGHTS["regulatory"]
        + tech_score * WEIGHTS["technical"]
    )

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
# ROI ENGINE — Phase 4B
# ============================================================================

def compute_roi(
    num_lines,
    num_facilities,
    changeovers_per_week,
    clearance_duration,
    labor_rate,
    time_savings_pct,
    first_line_cost,
    additional_line_cost,
):
    """
    Compute current annual cost, projected post-rollout cost, savings, and
    payback period. Every input above can be the simulator default or the
    user's override from the Advanced section.
    """
    hours_per_clearance = DURATION_TO_HOURS[clearance_duration]

    # Annual clearance events across the whole estate
    annual_clearance_events = num_lines * changeovers_per_week * WEEKS_PER_YEAR

    # Labor hours per event (operator + QA witness)
    labor_hours_per_event = hours_per_clearance * NUM_OPERATORS_PER_CLEARANCE

    # Current annual line clearance labor cost
    current_annual_cost = (
        annual_clearance_events * labor_hours_per_event * labor_rate
    )

    # Post-rollout cost: time savings only applied to clearance duration
    post_rollout_cost = current_annual_cost * (1 - time_savings_pct / 100)
    annual_savings = current_annual_cost - post_rollout_cost

    # Deployment cost: first line per facility full price; remaining lines
    # in same facility get the discounted rate
    # (assumes lines are roughly evenly distributed across facilities)
    lines_per_facility = max(1, num_lines / num_facilities)
    deployment_cost = (
        num_facilities * first_line_cost
        + num_facilities * (lines_per_facility - 1) * additional_line_cost
    )

    # Payback in months
    if annual_savings > 0:
        payback_months = (deployment_cost / annual_savings) * 12
    else:
        payback_months = None  # no savings = no payback

    return {
        "annual_events":        int(annual_clearance_events),
        "current_annual_cost":  current_annual_cost,
        "post_rollout_cost":    post_rollout_cost,
        "annual_savings":       annual_savings,
        "deployment_cost":      deployment_cost,
        "payback_months":       payback_months,
    }


# ============================================================================
# UI HANDLER
# ============================================================================

def _fmt_money(x):
    """Format a dollar amount with thousands separators and no decimals."""
    return f"${x:,.0f}"


def process_form(
    num_lines, num_facilities, annual_volume, product_type,
    current_method, clearance_duration, changeovers_per_week, deviation_frequency,
    mes_system, ebr_system, equipment_age,
    inspection_outcome, validation_maturity,
    operator_familiarity, prior_attempt,
    # Advanced assumptions (with defaults pre-filled in the UI)
    labor_rate, time_savings_pct, first_line_cost, additional_line_cost,
):
    score = compute_readiness_score(
        current_method, clearance_duration, deviation_frequency,
        operator_familiarity, prior_attempt,
        inspection_outcome, validation_maturity,
        mes_system, ebr_system, equipment_age,
    )

    roi = compute_roi(
        num_lines, num_facilities, changeovers_per_week, clearance_duration,
        labor_rate, time_savings_pct, first_line_cost, additional_line_cost,
    )

    payback_text = (
        f"**{roi['payback_months']:.1f} months**"
        if roi["payback_months"] is not None
        else "Not applicable (no projected savings)"
    )

    summary = f"""
## Readiness Assessment

### Overall Readiness Score: **{score['total']} / 100**

### Verdict: **{score['verdict_label']}**
{score['verdict_message']}

---

### Sub-score Breakdown

| Category | Weight | Score |
|---|---|---|
| Process readiness | 30% | **{score['process']}** / 100 |
| Organizational readiness | 30% | **{score['organizational']}** / 100 |
| Regulatory readiness | 25% | **{score['regulatory']}** / 100 |
| Technical readiness | 15% | **{score['technical']}** / 100 |

---

## Financial Projection (ROI)

### Headline numbers

| Metric | Value |
|---|---|
| Annual line clearance events | **{roi['annual_events']:,}** |
| Current annual line clearance cost | **{_fmt_money(roi['current_annual_cost'])}** |
| Projected post-rollout annual cost | **{_fmt_money(roi['post_rollout_cost'])}** |
| **Annual savings** | **{_fmt_money(roi['annual_savings'])}** |
| Estimated deployment cost | **{_fmt_money(roi['deployment_cost'])}** |
| **Payback period** | {payback_text} |

### How this was calculated

- **Annual clearance events:** {num_lines} lines × {changeovers_per_week} changeovers/week × 48 production weeks/year
- **Labor hours per event:** {DURATION_TO_HOURS[clearance_duration]} hours × 2 operators (operator + QA witness, per GMP)
- **Labor rate used:** {_fmt_money(labor_rate)}/hour (fully-loaded — adjustable in Advanced section)
- **Time savings applied:** {time_savings_pct}% reduction in clearance time (Catalyx publishes 85%; this default is conservatively halved)
- **Deployment cost:** {_fmt_money(first_line_cost)} for the first line in each of {num_facilities} facilities, plus {_fmt_money(additional_line_cost)} for each additional line in those facilities

*These numbers are estimates built on conservative industry-typical assumptions.
Adjust any of them in the "Advanced assumptions" section above and re-run to
see how the financials shift under your own assumptions.*

---

*Coming next: risk heatmap (Phase 4C), tailored next-steps recommendations
(Phase 4D), and visual charts + PDF executive summary (Phases 5 and 6).*
"""
    return summary


# ============================================================================
# UI
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

*Currently in development. Phase 4B — readiness scoring + ROI projection.
Risk heatmap, next-steps, charts, and PDF export are coming in later phases.*

---

### Instructions
Answer the 15 questions below. All fields have sensible defaults — adjust
those that apply to your situation. Optionally expand "Advanced assumptions"
to override the financial inputs. Click **Submit** to see your full assessment.
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

    with gr.Accordion("Advanced assumptions (optional — override defaults)", open=False):
        gr.Markdown(
            "These defaults come from publicly available industry data. "
            "Adjust any of them to reflect your own assumptions, then re-run."
        )
        labor_rate = gr.Slider(
            label="Fully-loaded operator labor rate (USD per hour)",
            minimum=20, maximum=150, value=DEFAULT_LABOR_RATE_USD_PER_HOUR, step=5,
        )
        time_savings_pct = gr.Slider(
            label="Expected time savings from OpenLine (%)",
            minimum=10, maximum=85, value=DEFAULT_TIME_SAVINGS_PCT, step=5,
        )
        first_line_cost = gr.Slider(
            label="First line deployment cost per facility (USD)",
            minimum=30_000, maximum=200_000,
            value=DEFAULT_FIRST_LINE_COST_USD, step=5_000,
        )
        additional_line_cost = gr.Slider(
            label="Additional line deployment cost (same facility, USD)",
            minimum=20_000, maximum=150_000,
            value=DEFAULT_ADDITIONAL_LINE_COST_USD, step=5_000,
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
            labor_rate, time_savings_pct, first_line_cost, additional_line_cost,
        ],
        outputs=output,
    )


if __name__ == "__main__":
    demo.launch()