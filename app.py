import gradio as gr

# ============================================================
# OpenLine Readiness Simulator
# Phase 3A: warm-up form with 3 placeholder questions
# ============================================================

def process_form(num_lines, num_facilities, product_type):
    """
    Take the user's answers and return a simple summary.
    No math yet — just echo back what they entered.
    """
    summary = f"""
    ## Thank you — here's what you told us:

    - **Number of production lines:** {num_lines}
    - **Number of facilities:** {num_facilities}
    - **Primary product type:** {product_type}

    *(Phase 3A complete — the full 15-question form is coming next.)*
    """
    return summary


# Build the Gradio interface
with gr.Blocks(title="OpenLine Readiness Simulator") as demo:

    gr.Markdown("# OpenLine Readiness Simulator")
    gr.Markdown(
        "A free tool to help pharma factories assess their readiness "
        "to roll out AI-powered line clearance. "
        "*(Currently in development — Phase 3A.)*"
    )

    gr.Markdown("### Section 1: Factory Profile")

    num_lines = gr.Number(
        label="Number of production lines in scope for rollout",
        value=5,
        minimum=1,
    )

    num_facilities = gr.Number(
        label="Number of facilities involved",
        value=1,
        minimum=1,
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

    submit_btn = gr.Button("Submit", variant="primary")

    output = gr.Markdown()

    submit_btn.click(
        fn=process_form,
        inputs=[num_lines, num_facilities, product_type],
        outputs=output,
    )


if __name__ == "__main__":
    demo.launch()