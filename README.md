# Camper Survey Extraction Tool (Camp Belknap - Azure OpenAI Version)

This tool extracts handwritten and circled data from multi-page scanned camper surveys (PDF format) and compiles them into a structured CSV file. It utilizes **Microsoft Azure OpenAI (GPT-4o-mini)** to parse the document pages and return strict structured data.

---

## How It Works

1. **Loads PDF & Converts to Images**: Each survey in the PDF is exactly 2 pages. Since Azure OpenAI's multimodal chat completions API requires image inputs, the Python script uses **`pymupdf`** to render each PDF page into a PNG image in memory.
2. **AI Processing**: Every 2 pages (1 survey), the script sends the two PNG images (as base64-encoded strings) to the Azure OpenAI service.
3. **Structured Extraction**: Azure OpenAI interprets the circles, checkboxes, tables, and handwriting, mapping the values into a strict data schema using **Pydantic Structured Outputs**.
4. **CSV Compilation**: The script compiles all responses into a pandas DataFrame and saves it as `survey_results.csv`.

---

## Installation

### 1. Prerequisites
Ensure you have **Python 3.9+** installed on your machine. You can verify this by running:
```bash
python --version
```

### 2. Install Dependencies
Navigate to this project directory and install the required packages:
```bash
pip install -r requirements.txt
```

---

## Web Interface (Easiest for Non-Technical Users)

We have built a sleek, user-friendly local web dashboard for camp staff. 

### How to Start the Web Interface:
1. **Windows Launcher (Easiest)**:
   Double-click the `Run_Survey_Tool.bat` file in the project folder.
2. **Via Command Line**:
   Run the following command in the project directory:
   ```bash
   python -m streamlit run app.py
   ```
This will automatically open your web browser to `http://localhost:8501`.

### Key Features of the Web App:
* **One-time Settings**: Enter your API credentials (either standard OpenAI or Azure OpenAI) once in the sidebar and click **"Save Settings"**; they will be remembered forever.
* **Drag-and-Drop Uploader**: Drag your scanned PDF directly into the browser.
* **Progress Tracking**: See a live progress bar and extraction logs as the AI reads the surveys.
* **Data Preview**: Inspect the extracted names, ratings, and comments in a neat spreadsheet format.
* **Download Button**: Download the finalized CSV file with a single click (a copy is also saved automatically to your `SurveyOutput` folder).

---

## Setup Credentials (CLI only)

To run this tool, you can use either a standard **OpenAI API Key** or an active **Azure OpenAI** resource with a **gpt-4o-mini** (or gpt-4o) model.

### Option A: Standard OpenAI (Direct)
You only need to set one environment variable in your terminal:
* **PowerShell (Windows)**:
  ```powershell
  $env:OPENAI_API_KEY="sk-proj-your_api_key_here"
  ```
* **Command Prompt (Windows)**:
  ```cmd
  set OPENAI_API_KEY=sk-proj-your_api_key_here
  ```

### Option B: Azure OpenAI
You need three credentials set as environment variables:
* **Azure Endpoint**: The URL of your Azure OpenAI resource.
* **API Key**: The access key for your Azure OpenAI resource.
* **Deployment Name**: The name of the deployment containing the model (e.g. `gpt-4o-mini`).

* **PowerShell (Windows)**:
  ```powershell
  $env:AZURE_OPENAI_API_KEY="your_api_key_here"
  $env:AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
  $env:AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o-mini"
  ```
* **Command Prompt (Windows)**:
  ```cmd
  set AZURE_OPENAI_API_KEY=your_api_key_here
  set AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
  set AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
  ```

---

## Usage

Place your scanned PDF containing the surveys in the project folder (or specify its path), then run:

```bash
python extract_surveys.py <path_to_scanned_surveys.pdf>
```

### Options:
* `-o`, `--output`: Change the output CSV filename (default is `../SurveyOutput/survey_results.csv` relative to the script's directory). The script will automatically create the `SurveyOutput` folder if it doesn't exist.
* `--api-key`: Pass the API key directly (instead of using environment variables).
* `--endpoint`: Pass the Azure endpoint directly (for Azure OpenAI).
* `--deployment`: Pass the Azure deployment name or standard model name directly (e.g. `gpt-4o-mini`).
* `--api-version`: Specify a different Azure API version (default is `2024-08-01-preview`).

### Example Command:
```bash
python extract_surveys.py "../SurveyInput/1 (1).pdf"
```

---

## Output Data Structure

The generated CSV will contain the following columns:
* `camper_name` (e.g. Grant Braasch)
* `division` (e.g. Juniors)
* `cabin` (e.g. H)
* `q1_cabin_rating` to `q3_camp_rating` (Cabin, Division, Camp ratings from 1-5)
* `q4_monday` to `q4_2nd_thursday` (Day-by-day ratings from 1-11, or 'NA')
* `q5_favorite_part_of_day` (Meals, General Swim, Siesta, etc.)
* `q6_plays_sport` (Yes/No)
* `q7_plays_sport_at_camp` (Yes/No)
* `q8_favorite_camp_activities` (List of activities selected, e.g., `['Baseball', 'Street Hockey', "Adams' Cup"]`)
* `q9_new_activities_tried` (0-10)
* `q10_tried_activity_not_best_at` (Yes/No)
* `q11_inclusion_rating` to `q16_recommend_camp` (Social/camp feedback ratings)
* `q17_additional_comments` (Transcription of the comments section)
