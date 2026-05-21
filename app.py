import gradio as gr

def greet(name):
    if not name:
        return "Welcome to the OpenLine Readiness Simulator! (Project in progress — Phase 2 complete)"
    return f"Hello {name}! Welcome to the OpenLine Readiness Simulator. (Project in progress — Phase 2 complete)"

demo = gr.Interface(
    fn=greet,
    inputs=gr.Textbox(label="Your name (optional)"),
    outputs=gr.Textbox(label="Message"),
    title="OpenLine Readiness Simulator",
    description="A free tool to help pharma factories assess readiness for AI-powered line clearance rollout. — Under construction.",
)

demo.launch()