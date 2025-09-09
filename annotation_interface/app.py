#!/usr/bin/env python3
"""
Custom Data Annotation Interface for Ansible Log Error Annotations
"""

import gradio as gr
import json
import os
from datetime import datetime
from typing import Tuple


class DataAnnotationApp:
    def __init__(self, data_file: str, feedback_dir: str = "data"):
        self.data_file = data_file
        self.feedback_dir = feedback_dir
        self.feedback_file = os.path.join(feedback_dir, "annotation_feedback.json")
        self.current_index = 0
        self.data = []
        self.feedback_data = []

        # Ensure data directory exists
        os.makedirs(self.feedback_dir, exist_ok=True)

        self.load_data()
        self.load_feedback()

    def load_data(self):
        """Load the pipeline output data."""
        try:
            with open(self.data_file, "r") as f:
                self.data = json.load(f)
            # print(f"Loaded {len(self.data)} data entries")
        except Exception as e:
            print(f"Error loading data: {e}")
            self.data = []

    def load_feedback(self):
        """Load existing feedback data."""
        try:
            if os.path.exists(self.feedback_file):
                with open(self.feedback_file, "r") as f:
                    self.feedback_data = json.load(f)
            else:
                self.feedback_data = []
        except Exception as e:
            print(f"Error loading feedback: {e}")
            self.feedback_data = []

    def save_feedback(self, feedback: str) -> str:
        """Save feedback for current data entry."""
        if not self.data:
            return "No data available"

        current_entry = self.data[self.current_index]

        # Create feedback entry
        feedback_entry = {
            "timestamp": datetime.now().isoformat(),
            "index": self.current_index,
            "filename": current_entry.get("filename", ""),
            "line_number": current_entry.get("line_number", ""),
            "feedback": feedback,
            "summary": current_entry.get("summary", "")[:100] + "..."
            if len(current_entry.get("summary", "")) > 100
            else current_entry.get("summary", ""),
        }

        # Remove any existing feedback for this entry
        self.feedback_data = [
            f for f in self.feedback_data if f["index"] != self.current_index
        ]

        # Add new feedback if not empty
        if feedback.strip():
            self.feedback_data.append(feedback_entry)

        # Save to file
        try:
            with open(self.feedback_file, "w") as f:
                json.dump(self.feedback_data, f, indent=2)
            return f"Feedback saved for entry {self.current_index + 1}"
        except Exception as e:
            return f"Error saving feedback: {e}"

    def get_current_entry(self) -> Tuple[str, str, str, str, str, str]:
        """Get current data entry for display."""
        if not self.data:
            return (
                "No data",
                "No data",
                "No data",
                "",
                "0 / 0",
                self.get_feedback_table(),
            )

        entry = self.data[self.current_index]

        # Format error log with syntax highlighting
        log_content = entry.get("line_content", "No log content")

        # Format summary
        summary = entry.get("summary", "No summary available")

        # For now, use a placeholder for step-by-step solution
        # In the future, you can extend this to fetch from your database or add it to your JSON
        step_by_step = entry.get(
            "step_by_step_solution",
            "Step-by-step solution not available for this entry.\n\n"
            "This would typically contain:\n"
            "1. Problem identification\n"
            "2. Root cause analysis\n"
            "3. Recommended solution steps\n"
            "4. Prevention measures",
        )

        # Get existing feedback for this entry
        existing_feedback = ""
        for f in self.feedback_data:
            if f["index"] == self.current_index:
                existing_feedback = f["feedback"]
                break

        # Navigation info
        nav_info = f"{self.current_index + 1} / {len(self.data)}"

        return (
            log_content,
            summary,
            step_by_step,
            existing_feedback,
            nav_info,
            self.get_feedback_table(),
        )

    def navigate(self, direction: int) -> Tuple[str, str, str, str, str, str]:
        """Navigate through data entries."""
        if not self.data:
            return self.get_current_entry()

        self.current_index = max(
            0, min(len(self.data) - 1, self.current_index + direction)
        )
        return self.get_current_entry()

    def go_to_index(self, index: int) -> Tuple[str, str, str, str, str, str]:
        """Jump to specific index."""
        if not self.data:
            return self.get_current_entry()

        self.current_index = max(0, min(len(self.data) - 1, index))
        return self.get_current_entry()

    def get_feedback_table(self) -> str:
        """Generate HTML table of all feedback."""
        if not self.feedback_data:
            return "<div style='padding: 20px; text-align: center; color: #94a3b8; background-color: #1e293b; border: 1px solid #475569; border-radius: 8px;'>No feedback entries yet</div>"

        # Sort by timestamp (most recent first)
        sorted_feedback = sorted(
            self.feedback_data, key=lambda x: x["timestamp"], reverse=True
        )

        html = """
        <div style="max-height: 300px; overflow-y: auto; border: 1px solid #475569; border-radius: 8px; background-color: #1e293b;">
            <table style="width: 100%; border-collapse: collapse; font-size: 12px; background-color: #1e293b; color: #e2e8f0;">
                <thead style="background-color: #334155; position: sticky; top: 0;">
                    <tr>
                        <th style="padding: 8px; border: 1px solid #475569; color: #f1f5f9; font-weight: 600;">Index</th>
                        <th style="padding: 8px; border: 1px solid #475569; color: #f1f5f9; font-weight: 600;">File</th>
                        <th style="padding: 8px; border: 1px solid #475569; color: #f1f5f9; font-weight: 600;">Summary</th>
                        <th style="padding: 8px; border: 1px solid #475569; color: #f1f5f9; font-weight: 600;">Feedback</th>
                        <th style="padding: 8px; border: 1px solid #475569; color: #f1f5f9; font-weight: 600;">Time</th>
                    </tr>
                </thead>
                <tbody>
        """

        for feedback in sorted_feedback:
            timestamp = datetime.fromisoformat(feedback["timestamp"]).strftime(
                "%m/%d %H:%M"
            )
            feedback_text = (
                feedback["feedback"][:50] + "..."
                if len(feedback["feedback"]) > 50
                else feedback["feedback"]
            )

            html += f"""
                <tr style="border-bottom: 1px solid #475569; background-color: #1e293b;" onmouseover="this.style.backgroundColor='#334155'" onmouseout="this.style.backgroundColor='#1e293b'">
                    <td style="padding: 8px; border: 1px solid #475569; color: #e2e8f0;">{feedback["index"] + 1}</td>
                    <td style="padding: 8px; border: 1px solid #475569; color: #e2e8f0;" title="{feedback["filename"]}">{feedback["filename"][:20]}...</td>
                    <td style="padding: 8px; border: 1px solid #475569; color: #e2e8f0;" title="{feedback["summary"]}">{feedback["summary"]}</td>
                    <td style="padding: 8px; border: 1px solid #475569; color: #e2e8f0;" title="{feedback["feedback"]}">{feedback_text}</td>
                    <td style="padding: 8px; border: 1px solid #475569; color: #e2e8f0;">{timestamp}</td>
                </tr>
            """

        html += """
                </tbody>
            </table>
        </div>
        """
        return html


def create_app():
    """Create the Gradio interface."""
    # Initialize the app
    data_file = "/home/ikatav/Projects/ansible-logs-folders/ansible-logs/data/logs/failed_lines_extracted_with_summaries.json"
    app = DataAnnotationApp(data_file)

    # Custom CSS for dark theme
    css = """
    .error-log { 
        font-family: 'JetBrains Mono', 'Consolas', 'Monaco', monospace; 
        font-size: 12px; 
        line-height: 1.5; 
        background-color: #0f172a !important; 
        color: #e2e8f0 !important; 
        padding: 16px; 
        border-radius: 8px; 
        border: 1px solid #334155 !important;
        max-height: 600px;
        overflow-y: auto;
    }
    .summary-box {
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #475569 !important;
        background-color: #1e293b !important;
        color: #e2e8f0 !important;
        line-height: 1.6;
    }
    .solution-box {
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #475569 !important;
        background-color: #1e293b !important;
        color: #e2e8f0 !important;
        line-height: 1.6;
        margin-top: 12px;
    }
    .feedback-box {
        min-height: 200px;
        background-color: #1e293b !important;
        color: #e2e8f0 !important;
        border: 1px solid #475569 !important;
    }
    .nav-button {
        min-width: 100px;
        margin: 6px;
        background-color: #475569 !important;
        color: #f1f5f9 !important;
        border: 1px solid #64748b !important;
    }
    .nav-button:hover {
        background-color: #64748b !important;
        color: #ffffff !important;
    }
    /* Dark theme for feedback table */
    table {
        background-color: #1e293b !important;
        color: #e2e8f0 !important;
    }
    th {
        background-color: #334155 !important;
        color: #f1f5f9 !important;
    }
    td {
        border-color: #475569 !important;
    }
    tr:hover {
        background-color: #334155 !important;
    }
    /* Override any light theme remnants */
    .gradio-container {
        background-color: #0f172a !important;
    }
    """

    with gr.Blocks(
        css=css,
        theme=gr.themes.Soft(
            primary_hue="indigo",
            secondary_hue="blue",
            neutral_hue="slate",
            font=gr.themes.GoogleFont("Inter"),
            font_mono=gr.themes.GoogleFont("JetBrains Mono"),
        ).set(
            body_background_fill="*neutral_950",
            body_text_color="*neutral_100",
            block_background_fill="*neutral_900",
            block_border_color="*neutral_700",
            input_background_fill="*neutral_800",
            button_primary_background_fill="*primary_600",
            button_primary_text_color="white",
        ),
        title="Ansible Log Annotation Interface",
    ) as interface:
        gr.Markdown("# Ansible Log Data Annotation Interface")
        gr.Markdown(
            "Annotate pipeline outputs with feedback on failure modes and solution quality."
        )

        # Navigation controls
        with gr.Row():
            with gr.Column(scale=1):
                prev_btn = gr.Button("← Previous (←)", elem_classes="nav-button")

            with gr.Column(scale=2):
                nav_info = gr.Textbox(
                    label="Position",
                    interactive=False,
                    value="Loading...",
                    container=False,
                )

            with gr.Column(scale=1):
                next_btn = gr.Button("Next (→)", elem_classes="nav-button")

        # Jump to specific entry
        with gr.Row():
            jump_input = gr.Number(
                label="Jump to entry", minimum=1, step=1, precision=0
            )
            jump_btn = gr.Button("Go")

        # Main content area
        with gr.Row():
            # Left column - Error Log
            with gr.Column(scale=2):
                gr.Markdown("## Input:")
                error_log = gr.Textbox(
                    label="Error Log",
                    lines=25,
                    elem_classes="error-log",
                    interactive=False,
                    show_copy_button=True,
                )

            # Center column - Summary and Solution
            with gr.Column(scale=2):
                gr.Markdown("## Outputs:")
                summary = gr.Textbox(
                    label="Summary",
                    lines=8,
                    elem_classes="summary-box",
                    interactive=False,
                )

                step_by_step = gr.Textbox(
                    label="Step-by-Step Solution",
                    lines=15,
                    elem_classes="solution-box",
                    interactive=False,
                )

            # Right column - Feedback
            with gr.Column(scale=2):
                feedback_text = gr.Textbox(
                    label="Feedback & Failure Mode Analysis",
                    lines=20,
                    placeholder="Describe any issues with the summary or solution:\n"
                    "- Is the summary accurate?\n"
                    "- Is the solution appropriate?\n"
                    "- What failure modes do you observe?\n"
                    "- Any missing information?",
                    elem_classes="feedback-box",
                )

                save_feedback_btn = gr.Button("Save Feedback", variant="primary")
                feedback_status = gr.Textbox(label="Status", interactive=False, lines=1)

        # Feedback table at the bottom
        with gr.Row():
            feedback_table = gr.HTML(label="Feedback History", value="Loading...")

        # Initialize the interface
        def init_interface():
            return app.get_current_entry()

        # Event handlers
        def handle_save_feedback(feedback):
            status = app.save_feedback(feedback)
            return status, app.get_feedback_table()

        def handle_navigate_prev():
            return app.navigate(-1)

        def handle_navigate_next():
            return app.navigate(1)

        def handle_jump(index):
            if index is not None:
                return app.go_to_index(int(index) - 1)  # Convert to 0-based index
            return app.get_current_entry()

        # Bind events
        interface.load(
            init_interface,
            outputs=[
                error_log,
                summary,
                step_by_step,
                feedback_text,
                nav_info,
                feedback_table,
            ],
        )

        prev_btn.click(
            handle_navigate_prev,
            outputs=[
                error_log,
                summary,
                step_by_step,
                feedback_text,
                nav_info,
                feedback_table,
            ],
        )

        next_btn.click(
            handle_navigate_next,
            outputs=[
                error_log,
                summary,
                step_by_step,
                feedback_text,
                nav_info,
                feedback_table,
            ],
        )

        jump_btn.click(
            handle_jump,
            inputs=[jump_input],
            outputs=[
                error_log,
                summary,
                step_by_step,
                feedback_text,
                nav_info,
                feedback_table,
            ],
        )

        save_feedback_btn.click(
            handle_save_feedback,
            inputs=[feedback_text],
            outputs=[feedback_status, feedback_table],
        )

    return interface


demo = create_app()
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7861, share=False, debug=True)
