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
    "Vault Pod & Secret Storage Issues",
    "Other"
]

# Global variable to store all alerts
all_alerts: List[Dict[str, Any]] = []


def extract_unique_label_keys(alerts: List[Dict[str, Any]]) -> List[str]:
    """Extract unique label keys from all alerts."""
    label_keys = set()
    for alert in alerts:
        labels = alert.get("labels", {})
        label_keys.update(labels.keys())
    return sorted(list(label_keys))


def extract_unique_label_values(alerts: List[Dict[str, Any]], label_key: str) -> List[str]:
    """Extract unique values for a specific label key from all alerts."""
    label_values = set()
    for alert in alerts:
        labels = alert.get("labels", {})
        if label_key in labels:
            label_values.add(labels[label_key])
    return sorted(list(label_values))


def filter_alerts_by_label(alerts: List[Dict[str, Any]], label_key: str, label_value: str) -> List[Dict[str, Any]]:
    """Filter alerts by a specific label key-value pair."""
    if not label_key or not label_value:
        return alerts
    
    filtered_alerts = []
    for alert in alerts:
        labels = alert.get("labels", {})
        if labels.get(label_key) == label_value:
            filtered_alerts.append(alert)
    
    return filtered_alerts


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
            response = await client.get(f"{BACKEND_URL}/grafana-alert/by-category/?category={category}")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Error fetching alerts for category {category}: {e}")
        return []


def format_alerts_for_display(alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format alerts data for display in Gradio."""
    if not alerts:
        return []
    
    formatted_data = []
    for alert in alerts:
        # Parse timestamp for sorting
        timestamp = alert.get("logTimestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
                sort_timestamp = dt
            except (ValueError, TypeError):
                formatted_timestamp = str(timestamp)
                sort_timestamp = datetime.min
        else:
            formatted_timestamp = "Unknown"
            sort_timestamp = datetime.min
        
        summary = alert.get("logSummary", "No summary available")
        classification = alert.get("logClassification", "Unclassified")
        
        formatted_data.append({
            "Summary": summary,
            "Timestamp": formatted_timestamp,  # Keep for details view
            "Classification": classification,  # Keep for details view
            "Sort_Timestamp": sort_timestamp,  # For sorting purposes
            "Full Alert": alert  # Store full alert data for later use
        })
    
    # Sort by timestamp (newest first)
    formatted_data.sort(key=lambda x: x["Sort_Timestamp"], reverse=True)
    
    return formatted_data


def on_category_change(category: str):
    """Handle category dropdown change."""
    if not category or category == "Select a category":
        return pd.DataFrame(columns=["Summary"]), "", gr.update(choices=["No label key"], value="No label key"), gr.update(choices=["No label value"], value="No label value")
    
    import asyncio
    
    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        alerts = loop.run_until_complete(fetch_alerts_by_category(category))
        formatted_data = format_alerts_for_display(alerts)
        
        # Store data globally
        global current_alerts_data, current_category_alerts, current_label_keys
        current_alerts_data = formatted_data
        current_category_alerts = alerts
        current_label_keys = extract_unique_label_keys(alerts)
        
        # Create DataFrame with only Summary column for display
        if formatted_data:
            display_df = pd.DataFrame([{"Summary": item["Summary"]} for item in formatted_data])
        else:
            display_df = pd.DataFrame(columns=["Summary"])
        
        # Update label key dropdown
        label_key_choices = ["No label key"] + current_label_keys
        label_key_update = gr.update(choices=label_key_choices, value="No label key")
        label_value_update = gr.update(choices=["No label value"], value="No label value")
        
        return display_df, "", label_key_update, label_value_update
    finally:
        loop.close()


def on_label_key_change(label_key: str):
    """Handle label key dropdown change."""
    global current_category_alerts
    
    if not label_key or label_key == "No label key" or not current_category_alerts:
        return gr.update(choices=["No label value"], value="No label value")
    
    # Extract unique values for the selected label key
    label_values = extract_unique_label_values(current_category_alerts, label_key)
    label_value_choices = ["No label value"] + label_values
    
    return gr.update(choices=label_value_choices, value="No label value")


def on_label_filter_change(label_key: str, label_value: str):
    """Handle label filtering when label key or value changes."""
    global current_category_alerts, current_alerts_data
    
    if not current_category_alerts:
        return pd.DataFrame(columns=["Summary"])
    
    # Apply label filtering if both key and value are selected
    if label_key and label_key != "No label key" and label_value and label_value != "No label value":
        filtered_alerts = filter_alerts_by_label(current_category_alerts, label_key, label_value)
    else:
        filtered_alerts = current_category_alerts
    
    # Format and update display
    formatted_data = format_alerts_for_display(filtered_alerts)
    current_alerts_data = formatted_data
    
    if formatted_data:
        display_df = pd.DataFrame([{"Summary": item["Summary"]} for item in formatted_data])
    else:
        display_df = pd.DataFrame(columns=["Summary"])
    
    return display_df


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


**Full Log Message:**
```
{log_message}
```

**Labels:**
{chr(10).join([f"- {k}: {v}" for k, v in full_alert.get("labels", {}).items()]) if full_alert.get("labels") else "No labels"}
    """
    
    return details.strip()


# Global variables to store current alerts data and filtering state
current_alerts_data = []
current_category_alerts = []  # Store alerts from current category
current_label_keys = []  # Store available label keys


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
                2. Optionally filter by labels using the dropdowns on the right
                3. Browse the log summaries table (sorted by timestamp)
                4. Click on any summary to view full log details
                """)
            
            with gr.Column(scale=1):
                label_key_dropdown = gr.Dropdown(
                    choices=["No label key"],
                    value="No label key",
                    label="Label Key",
                    info="Select a label key to filter by"
                )
                
                label_value_dropdown = gr.Dropdown(
                    choices=["No label value"],
                    value="No label value",
                    label="Label Value",
                    info="Select a label value to filter by"
                )
        
        with gr.Row():
            with gr.Column(scale=2):
                alerts_table = gr.Dataframe(
                    headers=["Summary"],
                    datatype=["str"],
                    interactive=False,
                    wrap=True,
                    # height=400,
                    label="Log Summaries"
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
            outputs=[alerts_table, log_details, label_key_dropdown, label_value_dropdown]
        )
        
        label_key_dropdown.change(
            fn=on_label_key_change,
            inputs=[label_key_dropdown],
            outputs=[label_value_dropdown]
        )
        
        label_value_dropdown.change(
            fn=on_label_filter_change,
            inputs=[label_key_dropdown, label_value_dropdown],
            outputs=[alerts_table]
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
        debug=True,             # Enable debug mode
    )


if __name__ == "__main__":
    main()

