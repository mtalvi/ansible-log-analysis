#!/usr/bin/env python3
"""
Custom Data Annotation Interface for Ansible Log Error Annotations
"""

import gradio as gr
import json
import os
from datetime import datetime
from typing import Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session


class DataAnnotationApp:
    def __init__(self, feedback_dir: str = "data/feedback"):
        self.feedback_dir = feedback_dir
        self.feedback_file = os.path.join(feedback_dir, "annotation.json")
        self.current_index = 0
        self.data = []
        self.all_data = []  # Store all data before cluster filtering
        self.feedback_data = []
        self.show_cluster_sample = False  # Toggle state for cluster sampling

        # Get table name from environment variable
        self.table_name = os.getenv("ALERTS_TABLE_NAME", "grafanaalert")

        # Initialize sync engine
        self.engine = create_engine(
            os.getenv("DATABASE_URL")
            .replace("+asyncpg", "")
            .replace("postgresql", "postgresql+psycopg2")
        )

        # Ensure data directory exists
        os.makedirs(self.feedback_dir, exist_ok=True)

        self.load_data()
        self.load_feedback()

    def load_data(self):
        """Load the pipeline output data from PostgreSQL."""
        try:
            with Session(self.engine) as session:
                # Use raw SQL to query the table dynamically
                query = text(f"""
                    SELECT 
                        id,
                        "logMessage",
                        "logSummary", 
                        "stepByStepSolution",
                        "contextForStepByStepSolution",
                        "logCluster",
                        "log_labels"
                    FROM {self.table_name}
                    ORDER BY id
                """)

                result = session.execute(query)
                rows = result.fetchall()

                # Convert to the expected data format
                self.all_data = []
                for row in rows:
                    # Parse labels JSON if it exists
                    labels = (
                        row.log_labels
                        if hasattr(row, "labels") and row.log_labels
                        else {}
                    )

                    data_entry = {
                        "id": row.id,
                        "filename": labels.get("filename", "unknown")
                        if isinstance(labels, dict)
                        else "unknown",
                        "line_number": labels.get("line_number", "")
                        if isinstance(labels, dict)
                        else "",
                        "logMessage": row.logMessage or "No log content",
                        "summary": row.logSummary or "No summary available",
                        "context_for_solution": row.contextForStepByStepSolution
                        or "No context available",
                        "step_by_step_solution": row.stepByStepSolution
                        or "No solution available",
                        "log_cluster": row.logCluster
                        if hasattr(row, "logCluster")
                        else None,
                    }
                    self.all_data.append(data_entry)

                # Initialize data with all entries
                self.data = self.all_data.copy()

                print(
                    f"Loaded {len(self.all_data)} data entries from table '{self.table_name}'"
                )
        except Exception as e:
            print(f"Error loading data from database table '{self.table_name}': {e}")
            self.all_data = []
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

    def toggle_cluster_sampling(
        self, show_sample: bool
    ) -> Tuple[str, str, str, str, str, str, str]:
        """Toggle between showing all rows or one sample per cluster."""
        self.show_cluster_sample = show_sample

        if show_sample:
            # Group by cluster and take one sample from each
            cluster_samples = {}
            for entry in self.all_data:
                cluster_id = entry.get("log_cluster")
                # If no cluster, treat each entry as its own cluster
                if cluster_id is None:
                    cluster_id = f"_no_cluster_{entry.get('id')}"

                # Keep only the first entry from each cluster
                if cluster_id not in cluster_samples:
                    cluster_samples[cluster_id] = entry

            self.data = list(cluster_samples.values())
            print(
                f"Cluster sampling enabled: Showing {len(self.data)} samples from {len(self.all_data)} total entries"
            )
        else:
            # Show all data
            self.data = self.all_data.copy()
            print(f"Cluster sampling disabled: Showing all {len(self.data)} entries")

        # Reset to first entry
        self.current_index = 0
        return self.get_current_entry()

    def save_feedback(self, feedback: str, golden_solution: str = "") -> str:
        """Save feedback and golden solution for current data entry."""
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
            "golden_solution": golden_solution,
            "logMessage": current_entry.get("logMessage", "No line context"),
        }

        # Remove any existing feedback for this entry
        self.feedback_data = [
            f for f in self.feedback_data if f["index"] != self.current_index
        ]

        # Add new feedback if not empty (either feedback or golden_solution)
        if feedback.strip() or golden_solution.strip():
            self.feedback_data.append(feedback_entry)

        # Save to file
        try:
            with open(self.feedback_file, "w") as f:
                json.dump(self.feedback_data, f, indent=2)
            return f"Feedback saved for entry {self.current_index + 1}"
        except Exception as e:
            return f"Error saving feedback: {e}"

    def get_current_entry(self) -> Tuple[str, str, str, str, str, str, str]:
        """Get current data entry for display."""
        if not self.data:
            return (
                "No data",
                "No data",
                "No data",
                "No data",
                "",
                "",
                "0 / 0",
            )

        entry = self.data[self.current_index]

        # Format error log with syntax highlighting
        log_content = entry.get("logMessage", "No log content")

        # Format summary
        summary = entry.get("summary", "No summary available")

        # Get context for solution
        context_for_solution = entry.get(
            "context_for_solution",
            "No context available",
        )

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

        # Get existing feedback and golden solution for this entry
        existing_feedback = ""
        existing_golden_solution = ""
        for f in self.feedback_data:
            if f["index"] == self.current_index:
                existing_feedback = f.get("feedback", "")
                existing_golden_solution = f.get("golden_solution", "")
                break

        # Navigation info
        nav_info = f"{self.current_index + 1} / {len(self.data)}"

        return (
            log_content,
            summary,
            context_for_solution,
            step_by_step,
            existing_feedback,
            existing_golden_solution,
            nav_info,
        )

    def navigate(self, direction: int) -> Tuple[str, str, str, str, str, str, str]:
        """Navigate through data entries."""
        if not self.data:
            return self.get_current_entry()

        self.current_index = max(
            0, min(len(self.data) - 1, self.current_index + direction)
        )
        return self.get_current_entry()

    def go_to_index(self, index: int) -> Tuple[str, str, str, str, str, str, str]:
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
                        <th style="padding: 8px; border: 1px solid #475569; color: #f1f5f9; font-weight: 600;">Log</th>
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
                    <td style="padding: 8px; border: 1px solid #475569; color: #e2e8f0;" title="{feedback["logMessage"]}">{feedback["logMessage"]}</td>
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
    feedback_dir = "data/feedback"
    app = DataAnnotationApp(feedback_dir)

    # Custom CSS for dark theme
    css = """
    .summary-box {
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #475569 !important;
        background-color: #1e293b !important;
        color: #e2e8f0 !important;
        line-height: 1.6;
    }
    .basic_box {
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
    .feedback-box {
        min-height: 200px;
        background-color: #1e293b !important;
        color: #e2e8f0 !important;
        border: 1px solid #475569 !important;
    }
    .nav-button {
        min-width: 60px;
        margin: 2px;
        background-color: #475569 !important;
        color: #f1f5f9 !important;
        border: 1px solid #64748b !important;
        padding: 4px 8px !important;
        font-size: 0.9em !important;
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

        # Compact navigation controls - all in one row
        with gr.Row():
            cluster_sample_toggle = gr.Checkbox(
                label="One sample per cluster",
                value=False,
                interactive=True,
                scale=2,
            )
            prev_btn = gr.Button(
                "← Prev",
                elem_classes="nav-button",
                scale=1,
            )
            nav_info = gr.Textbox(
                label="Position",
                interactive=False,
                value="Loading...",
                container=False,
                scale=1,
            )
            next_btn = gr.Button(
                "Next →",
                elem_classes="nav-button",
                scale=1,
            )
            jump_input = gr.Number(
                label="Jump to",
                minimum=1,
                step=1,
                precision=0,
                scale=1,
                container=False,
            )
            jump_btn = gr.Button(
                "Go",
                scale=1,
            )

        # Main content area - Reorganized into rows

        # Row 1: Inputs
        gr.Markdown("## 📥 Inputs")
        error_log = gr.Textbox(
            elem_classes="basic_box",
            label="Error Log",
            lines=5,
            max_lines=5,
            interactive=False,
            show_copy_button=True,
        )

        # Row 2: Outputs (toggleable)

        with gr.Row():
            gr.Markdown("## 🤖 AI-Generated Outputs")
            show_outputs_toggle = gr.Checkbox(
                label="🤖 Show AI-Generated Outputs",
                value=True,
                interactive=True,
            )
        with gr.Group(visible=True) as outputs_section:
            with gr.Row():
                show_summary_toggle = gr.Checkbox(
                    label="Show Summary",
                    value=True,
                    interactive=True,
                    scale=1,
                )
                show_context_toggle = gr.Checkbox(
                    label="Show Context for Solution",
                    value=True,
                    interactive=True,
                    scale=1,
                )
                show_solution_toggle = gr.Checkbox(
                    label="Show Step-by-Step Solution",
                    value=True,
                    interactive=True,
                    scale=1,
                )
            with gr.Column():
                with gr.Column():
                    gr.Markdown("### 🦾 Generated Summary")
                    summary = gr.Textbox(
                        lines=8,
                        elem_classes="basic_box",
                        visible=True,
                        show_label=False,
                    )

                with gr.Column():
                    gr.Markdown("### 🔍 Context for Solution")
                    context_for_solution = gr.Textbox(
                        elem_classes="basic_box",
                        show_label=False,
                        lines=8,
                        max_lines=8,
                        interactive=False,
                        show_copy_button=True,
                    )

                with gr.Column():
                    gr.Markdown("### 🦾 Step-by-Step Solution")
                    step_by_step = gr.Markdown(
                        value="",
                        label="🤖 Generated Step-by-Step Solution",
                        elem_classes="basic_box",
                        visible=True,
                    )

        # Row 3: Feedback columns
        gr.Markdown("## 📝 Human Annotations")

        with gr.Row():
            annotation_view_toggle = gr.Radio(
                choices=["Feedback & Failure Mode", "Golden Solution"],
                value="Feedback & Failure Mode",
                label="📝 Human Annotations",
                interactive=True,
                scale=1,
            )

        with gr.Row():
            with gr.Column(scale=1):
                feedback_text = gr.Textbox(
                    label="Feedback & Failure Mode Analysis",
                    lines=15,
                    placeholder="Describe any issues with the summary or solution:\n"
                    "- Is the summary accurate?\n"
                    "- Is the solution appropriate?\n"
                    "- What failure modes do you observe?\n"
                    "- Any missing information?",
                    elem_classes="feedback-box",
                    visible=True,
                )

                golden_solution_text = gr.Textbox(
                    label="Golden Step-by-Step Solution (Optional)",
                    lines=15,
                    placeholder="Provide your golden/ideal step-by-step solution:\n"
                    "1. Clear problem identification\n"
                    "2. Root cause analysis\n"
                    "3. Step-by-step solution\n"
                    "4. Prevention measures\n\n"
                    "This will be saved alongside your feedback for comparison with AI-generated solutions.",
                    elem_classes="feedback-box",
                    visible=False,
                )

        # Save feedback button and status
        with gr.Row():
            save_feedback_btn = gr.Button(
                "💾 Save Feedback", variant="primary", scale=1
            )
            feedback_status = gr.Textbox(
                label="Status", interactive=False, lines=1, scale=2
            )

        # Initialize the interface
        def init_interface():
            return app.get_current_entry()

        # Event handlers
        def handle_save_feedback(feedback, golden_solution):
            status = app.save_feedback(feedback, golden_solution)
            return status

        def handle_navigate_prev(
            show_outputs, show_summary, show_context, show_solution
        ):
            (
                log_content,
                summary_content,
                context_content,
                step_content,
                feedback,
                golden,
                nav,
            ) = app.navigate(-1)
            # Return content updates with visibility + preserved toggle states
            return (
                log_content,  # error_log
                gr.update(
                    value=summary_content, visible=show_summary
                ),  # summary with visibility
                gr.update(
                    value=context_content, visible=show_context
                ),  # context_for_solution with visibility
                gr.update(
                    value=step_content, visible=show_solution
                ),  # step_by_step with visibility
                feedback,  # feedback_text
                golden,  # golden_solution_text
                nav,  # nav_info
                show_outputs,  # preserve show_outputs_toggle
                show_summary,  # preserve show_summary_toggle
                show_context,  # preserve show_context_toggle
                show_solution,  # preserve show_solution_toggle
                gr.update(visible=show_outputs),  # outputs_section visibility
            )

        def handle_navigate_next(
            show_outputs, show_summary, show_context, show_solution
        ):
            (
                log_content,
                summary_content,
                context_content,
                step_content,
                feedback,
                golden,
                nav,
            ) = app.navigate(1)
            # Return content updates with visibility + preserved toggle states
            return (
                log_content,  # error_log
                gr.update(
                    value=summary_content, visible=show_summary
                ),  # summary with visibility
                gr.update(
                    value=context_content, visible=show_context
                ),  # context_for_solution with visibility
                gr.update(
                    value=step_content, visible=show_solution
                ),  # step_by_step with visibility
                feedback,  # feedback_text
                golden,  # golden_solution_text
                nav,  # nav_info
                show_outputs,  # preserve show_outputs_toggle
                show_summary,  # preserve show_summary_toggle
                show_context,  # preserve show_context_toggle
                show_solution,  # preserve show_solution_toggle
                gr.update(visible=show_outputs),  # outputs_section visibility
            )

        def handle_jump(index, show_outputs, show_summary, show_context, show_solution):
            if index is not None:
                (
                    log_content,
                    summary_content,
                    context_content,
                    step_content,
                    feedback,
                    golden,
                    nav,
                ) = app.go_to_index(int(index) - 1)
            else:
                (
                    log_content,
                    summary_content,
                    context_content,
                    step_content,
                    feedback,
                    golden,
                    nav,
                ) = app.get_current_entry()
            # Return content updates with visibility + preserved toggle states
            return (
                log_content,  # error_log
                gr.update(
                    value=summary_content, visible=show_summary
                ),  # summary with visibility
                gr.update(
                    value=context_content, visible=show_context
                ),  # context_for_solution with visibility
                gr.update(
                    value=step_content, visible=show_solution
                ),  # step_by_step with visibility
                feedback,  # feedback_text
                golden,  # golden_solution_text
                nav,  # nav_info
                show_outputs,  # preserve show_outputs_toggle
                show_summary,  # preserve show_summary_toggle
                show_context,  # preserve show_context_toggle
                show_solution,  # preserve show_solution_toggle
                gr.update(visible=show_outputs),  # outputs_section visibility
            )

        def handle_cluster_toggle(show_sample):
            return app.toggle_cluster_sampling(show_sample)

        def handle_outputs_toggle(show_outputs):
            return gr.update(visible=show_outputs)

        def handle_summary_toggle(show_summary):
            return gr.update(visible=show_summary)

        def handle_context_toggle(show_context):
            return gr.update(visible=show_context)

        def handle_solution_toggle(show_solution):
            return gr.update(visible=show_solution)

        def handle_annotation_view_toggle(view_selection):
            """Toggle between feedback and golden solution views."""
            show_feedback = view_selection == "Feedback & Failure Mode"
            show_golden = view_selection == "Golden Solution"
            return (
                gr.update(visible=show_feedback),  # feedback_text
                gr.update(visible=show_golden),  # golden_solution_text
            )

        # Bind events
        interface.load(
            init_interface,
            outputs=[
                error_log,
                summary,
                context_for_solution,
                step_by_step,
                feedback_text,
                golden_solution_text,
                nav_info,
            ],
        )

        prev_btn.click(
            handle_navigate_prev,
            inputs=[
                show_outputs_toggle,
                show_summary_toggle,
                show_context_toggle,
                show_solution_toggle,
            ],
            outputs=[
                error_log,
                summary,
                context_for_solution,
                step_by_step,
                feedback_text,
                golden_solution_text,
                nav_info,
                show_outputs_toggle,
                show_summary_toggle,
                show_context_toggle,
                show_solution_toggle,
                outputs_section,
            ],
        )

        next_btn.click(
            handle_navigate_next,
            inputs=[
                show_outputs_toggle,
                show_summary_toggle,
                show_context_toggle,
                show_solution_toggle,
            ],
            outputs=[
                error_log,
                summary,
                context_for_solution,
                step_by_step,
                feedback_text,
                golden_solution_text,
                nav_info,
                show_outputs_toggle,
                show_summary_toggle,
                show_context_toggle,
                show_solution_toggle,
                outputs_section,
            ],
        )

        jump_btn.click(
            handle_jump,
            inputs=[
                jump_input,
                show_outputs_toggle,
                show_summary_toggle,
                show_context_toggle,
                show_solution_toggle,
            ],
            outputs=[
                error_log,
                summary,
                context_for_solution,
                step_by_step,
                feedback_text,
                golden_solution_text,
                nav_info,
                show_outputs_toggle,
                show_summary_toggle,
                show_context_toggle,
                show_solution_toggle,
                outputs_section,
            ],
        )

        save_feedback_btn.click(
            handle_save_feedback,
            inputs=[feedback_text, golden_solution_text],
            outputs=[feedback_status],
        )

        cluster_sample_toggle.change(
            handle_cluster_toggle,
            inputs=[cluster_sample_toggle],
            outputs=[
                error_log,
                summary,
                context_for_solution,
                step_by_step,
                feedback_text,
                golden_solution_text,
                nav_info,
            ],
        )

        show_outputs_toggle.change(
            handle_outputs_toggle,
            inputs=[show_outputs_toggle],
            outputs=[outputs_section],
        )

        show_summary_toggle.change(
            handle_summary_toggle,
            inputs=[show_summary_toggle],
            outputs=[summary],
        )

        show_context_toggle.change(
            handle_context_toggle,
            inputs=[show_context_toggle],
            outputs=[context_for_solution],
        )

        show_solution_toggle.change(
            handle_solution_toggle,
            inputs=[show_solution_toggle],
            outputs=[step_by_step],
        )

        annotation_view_toggle.change(
            handle_annotation_view_toggle,
            inputs=[annotation_view_toggle],
            outputs=[feedback_text, golden_solution_text],
        )

    return interface


demo = create_app()
if __name__ == "__main__":
    demo.launch(
        server_name=os.getenv("GRADIO_SERVER_NAME", "0.0.0.0"),
        server_port=int(os.getenv("GRADIO_SERVER_PORT", 7861)),
        share=False,
        debug=True,
    )
