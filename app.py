import gradio as gr

# ============================================================
# OpenLine Readiness Simulator
# Phase 3B: Full 15-question questionnaire (no math yet)
# ============================================================

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

This simulator gives operations leaders, validation teams, and pre-sales engineers
a structured way to assess readiness in 10 minutes.

*Currently in development. This is Phase 3B — the input form. Scoring,
visualizations, and PDF export coming in later phases.*

---

### Instructions
Answer the 15 questions below across 5 sections. All fields have sensible
defaults — adjust the ones that apply to your situation. Click **Submit** at
the bottom to see a summary of your responses.
"""


def process_form(
    # Section 1
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
    Phase 3B: echo back the user's answers as a structured summary.
    No scoring or analysis yet — that's Phase 4.
    """
    summary = f"""
## ✅ Thank you — here's a summary of your responses

### Section 1: Factory Profile
- **Number of production lines in scope:** {num_lines}
- **Number of facilities involved:** {num_facilities}
- **Approximate annual production volume:** {annual_volume}
- **Primary product type:** {product_type}

### Section 2: Current Line Clearance Practice
- **Current method:** {current_method}
- **Average line clearance duration today:** {clearance_duration}
- **Average changeovers per line per week:** {changeovers_per_week}
- **Line clearance deviations in past 12 months:** {deviation_frequency}

### Section 3: IT and Integration Landscape
- **Existing MES system:** {mes_system}
- **Electronic batch record system:** {ebr_system}
- **Equipment and PLC age:** {equipment_age}

### Section 4: Regulatory and Quality Context
- **Last regulatory inspection outcome:** {inspection_outcome}
- **Computer system validation maturity:** {validation_maturity}

### Section 5: Workforce and Change-Management Context
- **Operator digital tool familiarity:** {operator_familiarity}
- **Prior line clearance digitization attempt:** {prior_attempt}

---

*Phase 3B complete. Next: in Phase 4, these answers will drive a Readiness
Score, ROI projection, risk heatmap, and a downloadable executive summary.*
"""
    return summary


# ============================================================
# Build the Gradio interface
# ============================================================

with gr.Blocks(
    title="OpenLine Readiness Simulator",
    theme=gr.themes.Soft(),
) as demo:

    gr.Markdown(INTRO_TEXT)

    # ----- Section 1: Factory Profile -----
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
            choices=[
                "Oral solid dose",
                "Injectable",
                "Biologic",
                "Medical device",
                "Other",
            ],
            value="Oral solid dose",
        )

    # ----- Section 2: Current Line Clearance Practice -----
    with gr.Accordion("Section 2: Current Line Clearance Practice", open=True):
        current_method = gr.Radio(
            label="Current line clearance method",
            choices=[
                "Fully paper-based",
                "Hybrid (some digital, some paper)",
                "Partially digitized",
                "Mostly digital",
            ],
            value="Hybrid (some digital, some paper)",
        )
        clearance_duration = gr.Radio(
            label="Average line clearance duration today",
            choices=[
                "Under 30 minutes",
                "30–60 minutes",
                "1–2 hours",
                "Over 2 hours",
            ],
            value="1–2 hours",
        )
        changeovers_per_week = gr.Slider(
            label="Average number of changeovers per line per week",
            minimum=1, maximum=30, value=5, step=1,
        )
        deviation_frequency = gr.Radio(
            label="Line clearance deviations in the past 12 months",
            choices=["None", "1–2", "3–5", "6 or more"],
            value="3–5",
        )

    # ----- Section 3: IT and Integration Landscape -----
    with gr.Accordion("Section 3: IT and Integration Landscape", open=True):
        mes_system = gr.Radio(
            label="Existing Manufacturing Execution System (MES)",
            choices=[
                "SAP",
                "Werum PAS-X",
                "Rockwell",
                "Tulip",
                "Other / Custom",
                "None",
            ],
            value="None",
        )
        ebr_system = gr.Radio(
            label="Electronic batch record (eBR) system in place",
            choices=["Yes", "Partial", "No"],
            value="Partial",
        )
        equipment_age = gr.Radio(
            label="Equipment and PLC age",
            choices=[
                "Mostly under 5 years",
                "Mixed (some new, some old)",
                "Mostly over 10 years",
            ],
            value="Mixed (some new, some old)",
        )

    # ----- Section 4: Regulatory and Quality Context -----
    with gr.Accordion("Section 4: Regulatory and Quality Context", open=True):
        inspection_outcome = gr.Radio(
            label="Last regulatory inspection outcome",
            choices=[
                "Clean (no observations)",
                "Minor observations",
                "Major observations",
                "Not applicable / never inspected",
            ],
            value="Minor observations",
        )
        validation_maturity = gr.Radio(
            label="Computer system validation maturity",
            choices=[
                "Mature (templates, dedicated team)",
                "Functional but ad-hoc",
                "Underdeveloped",
            ],
            value="Functional but ad-hoc",
        )

    # ----- Section 5: Workforce and Change-Management Context -----
    with gr.Accordion("Section 5: Workforce and Change-Management Context", open=True):
        operator_familiarity = gr.Radio(
            label="Operator digital tool familiarity",
            choices=["High", "Medium", "Low"],
            value="Medium",
        )
        prior_attempt = gr.Radio(
            label=(
                "Has your facility ever attempted a line clearance "
                "digitization project before?"
            ),
            choices=[
                "Yes — successful",
                "Yes — stalled or failed",
                "No — first attempt",
            ],
            value="No — first attempt",
        )

    # ----- Submit & output -----
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