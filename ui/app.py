import os
import gradio as gr
import httpx
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any


# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Log Categories (as defined in README)
LOG_CATEGORIES = [
    "GPU Autoscaling & Node Management Issues",
    "Cert-Manager & Certificate Creation Issues", 
    "KubeVirt VM Provisioning & PVC Issues",
    "Vault Pod & Secret Storage Issues"
]

# Global variable to store all alerts
all_alerts: List[Dict[str, Any]] = []


async def fetch_all_alerts() -> List[Dict[str, Any]]:
    """Fetch all Grafana alerts from the backend."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BACKEND_URL}/grafana-alert")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Error fetching all alerts: {e}")
        return []


async def fetch_alerts_by_category(category: str) -> List[Dict[str, Any]]:
    """Fetch alerts filtered by category from the backend."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BACKEND_URL}/by-category/{category}")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Error fetching alerts for category {category}: {e}")
        return []


def format_alerts_for_display(alerts: List[Dict[str, Any]]) -> pd.DataFrame:
    """Format alerts data for display in Gradio."""
    if not alerts:
        return pd.DataFrame(columns=["Timestamp", "Summary", "Classification"])
    
    formatted_data = []
    for alert in alerts:
        # Parse timestamp
        timestamp = alert.get("logTimestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                formatted_timestamp = str(timestamp)
        else:
            formatted_timestamp = "Unknown"
        
        summary = alert.get("logSummary", "No summary available")
        classification = alert.get("logClassification", "Unclassified")
        
        formatted_data.append({
            "Timestamp": formatted_timestamp,
            "Summary": summary,
            "Classification": classification,
            "Full Alert": alert  # Store full alert data for later use
        })
    
    # Sort by timestamp (newest first)
    formatted_data.sort(key=lambda x: x["Timestamp"], reverse=True)
    
    # Create DataFrame without the Full Alert column for display
    df = pd.DataFrame([{k: v for k, v in item.items() if k != "Full Alert"} for item in formatted_data])
    return df, formatted_data


def on_category_change(category: str):
    """Handle category dropdown change."""
    if not category or category == "Select a category":
        return pd.DataFrame(columns=["Timestamp", "Summary", "Classification"]), ""
    
    import asyncio
    
    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        alerts = loop.run_until_complete(fetch_alerts_by_category(category))
        df, formatted_data = format_alerts_for_display(alerts)
        
        # Store formatted data globally for log detail access
        global current_alerts_data
        current_alerts_data = formatted_data
        
        return df, ""
    finally:
        loop.close()


def on_log_select(evt: gr.SelectData):
    """Handle log summary selection to show full log message."""
    global current_alerts_data
    
    if not current_alerts_data or evt.index[0] >= len(current_alerts_data):
        return "No log details available."
    
    selected_alert = current_alerts_data[evt.index[0]]
    full_alert = selected_alert.get("Full Alert", {})
    
    log_message = full_alert.get("logMessage", "No log message available")
    
    # Format the detailed view
    details = f"""
**Timestamp:** {selected_alert.get("Timestamp", "Unknown")}
**Classification:** {selected_alert.get("Classification", "Unclassified")}
**Summary:** {selected_alert.get("Summary", "No summary")}

**Full Log Message:**
```
{log_message}
```

**Labels:**
{chr(10).join([f"- {k}: {v}" for k, v in full_alert.get("labels", {}).items()]) if full_alert.get("labels") else "No labels"}
    """
    
    return details.strip()


# Global variable to store current alerts data
current_alerts_data = []


def create_interface():
    """Create and configure the Gradio interface."""
    
    with gr.Blocks(title="Ansible Logs Viewer", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🔍 Ansible Logs Viewer")
        gr.Markdown("Browse and analyze Grafana alerts by category")
        
        with gr.Row():
            with gr.Column(scale=1):
                category_dropdown = gr.Dropdown(
                    choices=["Select a category"] + LOG_CATEGORIES,
                    value="Select a category",
                    label="Log Category",
                    info="Select a category to filter alerts"
                )
                
                # Info section
                gr.Markdown("""
                ### How to use:
                1. Select a log category from the dropdown
                2. Browse the alerts table (sorted by timestamp)
                3. Click on any row to view full log details
                """)
        
        with gr.Row():
            with gr.Column(scale=2):
                alerts_table = gr.Dataframe(
                    headers=["Timestamp", "Summary", "Classification"],
                    datatype=["str", "str", "str"],
                    interactive=False,
                    wrap=True,
                    height=400,
                    label="Alerts"
                )
            
            with gr.Column(scale=1):
                log_details = gr.Markdown(
                    value="Select an alert from the table to view details.",
                    label="Log Details"
                )
        
        # Event handlers
        category_dropdown.change(
            fn=on_category_change,
            inputs=[category_dropdown],
            outputs=[alerts_table, log_details]
        )
        
        alerts_table.select(
            fn=on_log_select,
            outputs=[log_details]
        )
        
        # Footer
        gr.Markdown("---")
        gr.Markdown("**Backend URL:** " + BACKEND_URL)
    
    return demo


def main():
    """Main function to launch the Gradio app."""
    print("🚀 Starting Ansible Logs Viewer...")
    print(f"Backend URL: {BACKEND_URL}")
    
    # Create and launch the interface
    demo = create_interface()
    
    # Launch the app
    demo.launch(
        server_name="0.0.0.0",  # Allow external connections
        server_port=7860,       # Default Gradio port
        share=False,            # Set to True for public sharing
        debug=True             # Enable debug mode
    )


if __name__ == "__main__":
    main()

