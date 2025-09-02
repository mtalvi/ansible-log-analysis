# Ansible Log Labeling Interface

A custom Gradio-based data labeling interface for annotating Ansible error log pipeline outputs.

## Features

- **Multi-panel Layout**: 
  - Error log display (left)
  - Summary in center
  - Step-by-step solution below summary
  - Feedback text area (right)

- **Navigation**:
  - Left/Right arrow keys for quick navigation
  - Jump to specific entries
  - Navigation counter

- **Feedback System**:
  - Open-ended feedback text area
  - Automatic saving to `data/labeling_feedback.json`
  - Persistent feedback table at bottom
  - Failure mode analysis support

- **Keyboard Shortcuts**:
  - `←` (Left Arrow): Previous entry
  - `→` (Right Arrow): Next entry

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the interface:
```bash
python app.py
```

3. Access the interface at: http://localhost:7860

## Data Structure

The interface expects JSON data in the format:
```json
[
  {
    "filename": "job_123.txt",
    "line_number": 100,
    "line_content": "error log content...",
    "summary": "Error summary...",
    "step_by_step_solution": "Optional step-by-step solution..."
  }
]
```

## Feedback Storage

Feedback is automatically saved to `data/labeling_feedback.json` with:
- Timestamp
- Entry index
- Filename reference
- User feedback text
- Associated summary (truncated)

## Usage Tips

1. Use the feedback area to note:
   - Summary accuracy issues
   - Solution appropriateness
   - Missing information
   - Observed failure modes

2. Navigate quickly using arrow keys
3. Use the feedback history table to track progress
4. Jump to specific entries using the number input
