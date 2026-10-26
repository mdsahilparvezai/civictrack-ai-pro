# CivicTrack AI Pro

Civic infrastructure issue reporting and public infrastructure/budget transparency dashboard.

A local-first Streamlit application for recording, exploring, and prioritizing civic infrastructure complaints (potholes, street lights, graffiti, water mains, etc.) alongside budget project tracking. AI features run entirely on your machine through local Ollama models — no cloud API keys required.

> **Note:** All sample data in this project is synthetic and created for demonstration purposes only. It is NOT verified official government data and does not represent real civic infrastructure, complaints, projects, or budgets.

---

## Problem Statement

Civic infrastructure issues — potholes, broken streetlights, graffiti, water main leaks, and damaged sidewalks — affect daily quality of life, but residents often have no simple, centralized way to report them, and municipalities lack transparent visibility into reported problems and budget spending. CivicTrack AI Pro provides a local demonstration platform where issues can be reported, categorized, prioritized, explored, and tracked alongside public budget projects.

---

## Key Features

| Feature | Status | Description |
|---------|--------|-------------|
| Dashboard | Verified | KPI cards (total complaints, pending, resolved, active projects), category bar chart, status donut chart, recent complaints table, and budget/projects preview. |
| Report an Issue | Verified | Form to submit a new civic issue with category, location, description, date, and optional photo upload. Issues are persisted to local JSON storage. |
| Issue Explorer | Verified | Searchable and filterable table of all complaints (sample + user-submitted) with filters for category, status, priority, and free-text search. |
| Budget & Projects | Verified | View sample civic budget projects with total budget, total spent, remaining budget, progress bars, and per-project status. |
| AI Assistant | Verified (requires Ollama) | Chat interface that answers questions about complaints using a local Ollama model (qwen3.5:4b) with retrieved complaint records as evidence. Cites issue IDs. |
| Photo upload & AI-assisted image analysis | Incomplete / not verified | Upload JPG, JPEG, or PNG photos for AI vision analysis. Requires a vision-capable Ollama model. Manual fallback is available if AI analysis fails. **Live vision analysis was not successfully completed during development.** |
| Automatic priority suggestions | Verified | Rule-based priority engine (Low/Medium/High/Critical) driven by category base priority and description keywords. AI-suggested priority from photo analysis can override, but user-edited fields are preserved. |
| Local data persistence | Verified | User-submitted complaints are saved to a local JSON file (`data/user_complaints.json`) so they survive Streamlit reruns and app restarts. |

---

## Tech Stack

- **Python 3.10+**
- **Streamlit** (`>=1.57`) — UI framework
- **Pandas** (`>=2.0`) — data handling
- **Plotly** (`>=5.0`) — charts (category bar, status donut)
- **requests** — HTTP client for Ollama API calls (used by the application; not listed in `requirements.txt`)
- **Pillow (PIL)** — image validation and handling (used by the application; not listed in `requirements.txt`)
- **Ollama** — local LLM server running on `http://localhost:11434`
- **Vision model**: `qwen3.5:4b` (configured in `civictrack-ai/pages/report_issue.py:148`)
- **Text/chat model**: `qwen3.5:4b` (configured in `civictrack-ai/ai_assistant.py:29`)

> Both the vision model and the text model use `qwen3.5:4b` in this environment. The `qwen2.5-vl:7b` model referenced in comments is not installed locally.

---

## Project Structure

```
civictrack-ai-pro/
├── civictrack-ai/
│   ├── app.py                          # Main Streamlit entry point: streamlit run app.py
│   ├── ai_assistant.py                 # Ollama chat logic for AI Assistant page
│   ├── ai_retrieval.py                 # Keyword-based complaint retrieval for AI Assistant
│   ├── requirements.txt                # Python dependencies (streamlit, pandas, plotly)
│   ├── .gitignore
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── dashboard.py                # Dashboard page (KPIs, charts, recent complaints)
│   │   ├── report_issue.py             # Report an Issue page (form, photo upload, vision AI)
│   │   ├── issue_explorer.py           # Issue Explorer page (searchable/filterable table)
│   │   ├── budget_projects.py          # Budget & Projects page
│   │   └── ai_assistant.py             # AI Assistant chat page
│   ├── components/
│   │   ├── __init__.py
│   │   ├── kpi_cards.py                # KPI card component
│   │   ├── charts.py                   # Plotly category and status charts
│   │   ├── complaints_table.py         # Searchable/filterable complaints table
│   │   ├── budget_projects.py          # Budget/project progress component
│   │   └── sidebar.py                  # Main navigation sidebar
│   ├── data/
│   │   ├── __init__.py
│   │   ├── complaint_storage.py        # Local JSON persistence for user complaints
│   │   ├── sample_data.py              # Synthetic sample complaints and projects
│   │   └── user_complaints.json        # Persisted user-submitted complaints (gitignored)
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_report_issue_image_analysis.py  # Tests for photo analysis error reporting
│   └── .venv/                          # Virtual environment (gitignored)
```

---

## Prerequisites

- **Python 3.10 or later**
- **Git** (for cloning the repository)
- **Ollama** installed and running locally (`ollama serve`)
- **Vision-capable Ollama model**: `qwen3.5:4b` is installed in this environment. If you need an alternative, pull `qwen2.5-vl:7b`, `llama3.2-vision:11b`, or `llava`.
- **Hardware**: Ollama models run on your local CPU/GPU. A vision model like `qwen3.5:4b` (4.2B parameters, ~3.3 GB) requires sufficient RAM to load the model into memory.

---

## Installation and Setup

Run these commands in **Windows PowerShell** from the repository root (`civictrack-ai-pro/`):

### 1. Clone the repository

```powershell
git clone https://github.com/mdsahilparvezai/civictrack-ai-pro.git
cd civictrack-ai-pro
```

### 2. Create and activate a virtual environment

```powershell
cd civictrack-ai
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Python dependencies

```powershell
pip install -r requirements.txt
```

> **Note:** `requirements.txt` lists `streamlit`, `pandas`, and `plotly`. The application also imports `requests` and `Pillow` (PIL), which are not listed in `requirements.txt`. If you get import errors for those, install them manually:
> ```powershell
> pip install requests Pillow
> ```

### 4. Install and start Ollama

Download Ollama from https://ollama.com if you do not have it, then:

```powershell
ollama serve
```

Leave this running in a separate terminal. In another terminal, pull the required model:

```powershell
ollama pull qwen3.5:4b
```

Verify the model is available:

```powershell
ollama list
```

### 5. Launch the app

From the `civictrack-ai/` directory with the virtual environment activated:

```powershell
streamlit run app.py
```

The app will open in your default browser at `http://localhost:8501`.

> **Important:** Run `streamlit run app.py` from the `civictrack-ai/` directory, not the repository root. The app imports modules like `pages.report_issue` and `data.complaint_storage`, which resolve relative to `civictrack-ai/`.

---

## AI Setup

### Text model (AI Assistant)

- **Model**: `qwen3.5:4b`
- **Endpoint**: `http://localhost:11434/api/chat`
- **Configured in**: `civictrack-ai/ai_assistant.py:27-29`
- **Pull command**: `ollama pull qwen3.5:4b`

The AI Assistant retrieves relevant complaints using keyword matching, sends them as evidence to the local Ollama model, and returns an answer with cited issue IDs. If Ollama is not running or the model is not pulled, the assistant shows a friendly error message instead of crashing.

### Vision model (Photo analysis)

- **Model**: `qwen3.5:4b` (vision-capable variant)
- **Endpoint**: `http://localhost:11434/api/chat`
- **Configured in**: `civictrack-ai/pages/report_issue.py:148-152`
- **Pull command**: `ollama pull qwen3.5:4b`

Photo-based reporting sends the uploaded image (base64-encoded) to the vision model. If the model is unavailable, the app falls back to manual entry — you can still enter category, description, and location yourself.

### Troubleshooting Ollama

| Problem | Likely cause | Fix |
|---------|-------------|-----|
| Connection refused | Ollama not running | Run `ollama serve` in a separate terminal |
| `model 'qwen3.5:4b' not found` | Model not pulled | Run `ollama pull qwen3.5:4b` |
| HTTP 404 on `/api/chat` | Wrong endpoint or model missing | Confirm Ollama is on port 11434 and the model is pulled |
| Request timeout | Model still loading or slow hardware | Wait for the model to load; increase timeout if needed |

---

## Photo-Based Reporting

1. Open the **Report an Issue** page.
2. Upload a JPG, JPEG, or PNG photo of the issue.
3. The image is previewed, then sent to the local Ollama vision model for analysis.
4. If analysis succeeds, the AI-suggested category, description, priority, and reason are populated into the form fields.
5. You can manually edit any AI-populated field before submitting.
6. If AI analysis fails (model missing, Ollama down, timeout), a warning appears and you can still enter all details manually and submit.

**Supported formats:** JPG, JPEG, PNG  
**Manual fallback:** Always available — photo analysis is optional.

---

## Data Storage and Privacy

- User-submitted complaints are stored locally in `civictrack-ai/data/user_complaints.json`.
- This JSON file is created automatically when you submit your first issue and persists across Streamlit reruns and app restarts.
- **This is local development storage only.** It is NOT reliable permanent cloud storage and will not survive a redeploy on Streamlit Community Cloud or similar platforms.
- The file is gitignored (`.gitignore` includes `data/user_complaints.json`) so your submitted complaints are not committed to version control.
- Sample complaints and projects are synthetic and bundled in `civictrack-ai/data/sample_data.py`.

---

## Testing

The repository contains one test file:

```
civictrack-ai/tests/test_report_issue_image_analysis.py
```

It verifies photo analysis error reporting using mocked Ollama responses:

1. **Missing model** — verifies Ollama's "model not found" error is surfaced with the model name.
2. **Genuine endpoint 404** — verifies a plain 404 (non-JSON body) falls back to `http_404`.
3. **Request uses chat endpoint and vision model** — verifies the request URL, model name, and base64 image payload.
4. **Success response shape** — verifies a successful 200 response is parsed into `category`, `description`, `priority`, and `reason`.

### Run the tests

From the `civictrack-ai/` directory with the virtual environment activated:

```powershell
python -m unittest tests.test_report_issue_image_analysis
```

Or run a specific test:

```powershell
python -m unittest tests.test_report_issue_image_analysis.TestAnalyzeImageWithVision.test_success_response_shape_parsed
```

> These tests use mocked HTTP responses and do not require Ollama to be running. They verify error handling and response parsing, not live AI analysis.

---

## Known Limitations and Future Improvements

- **Live vision analysis not verified**: The `qwen2.5-vl:7b` model referenced in original comments is not installed locally. The current `qwen3.5:4b` model is installed and has vision capability, but live photo analysis timed out during development and was not successfully verified end-to-end.
- **requirements.txt is incomplete**: `requests` and `Pillow` are imported by the application but not listed in `requirements.txt`. Install them manually if needed.
- **No persistent user accounts or authentication**: All complaints are stored in a single local JSON file with no user separation.
- **No cloud deployment**: The app is designed for local execution only. Streamlit Community Cloud deployment is not supported due to local JSON storage and Ollama dependency.
- **Sample data is synthetic**: All bundled complaint and project data is fictitious and for demonstration only.
- **AI responses are local and unfiltered**: The AI Assistant answers based only on retrieved complaint records, but responses should still be reviewed for accuracy.

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: No module named 'streamlit'` | Dependencies not installed | Run `pip install -r requirements.txt` from `civictrack-ai/` |
| `ModuleNotFoundError: No module named 'pages'` | Wrong working directory | Run `streamlit run app.py` from the `civictrack-ai/` directory, not the repo root |
| `ConnectionError` or `Connection refused` | Ollama not running | Start `ollama serve` in a separate terminal |
| `model 'qwen3.5:4b' not found` | Model not pulled | Run `ollama pull qwen3.5:4b` |
| HTTP 404 on photo analysis | Vision model missing or wrong endpoint | Confirm `qwen3.5:4b` is pulled and Ollama is on port 11434 |
| Streamlit session-state errors | Widget key conflicts after rerun | Refresh the browser page; session state resets on reload |
| Photo analysis times out | Model still loading or slow hardware | Wait for the model to load; use manual entry as fallback |

---

## GitHub Contribution / Development Instructions

1. **Fork the repository** on GitHub.
2. **Clone your fork** and create a new branch:
   ```powershell
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** following the existing code style and conventions.
4. **Run the tests** to verify nothing is broken:
   ```powershell
   python -m unittest tests.test_report_issue_image_analysis
   ```
5. **Run the app locally** to verify your changes work:
   ```powershell
   streamlit run app.py
   ```
6. **Commit your changes** with a clear message:
   ```powershell
   git add .
   git commit -m "Describe your change"
   ```
7. **Push to your fork** and open a pull request against `mdsahilparvezai/civictrack-ai-pro`.

Please do not commit the `.venv/`, `__pycache__/`, or `data/user_complaints.json` files — they are gitignored.

---

## License

No license has been specified for this repository. All rights are reserved by default under applicable copyright law. If you plan to use, modify, or distribute this code, please contact the repository owner to clarify licensing terms.

---

*CivicTrack AI Pro — Local-first civic infrastructure reporting with AI-assisted analysis.*