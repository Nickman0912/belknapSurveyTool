import os
import json
import pandas as pd
import streamlit as st
import fitz  # PyMuPDF
from openai import OpenAI, AzureOpenAI

# Import shared extraction logic from CLI script
from extract_surveys import CamperSurvey2026, LeaderSurvey2026, get_survey_images_base64, process_survey_chunk

# Set page configuration
st.set_page_config(
    page_title="Camp Belknap - Survey Extraction Tool",
    page_icon="🌲",
    layout="wide"
)

import base64

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Load generated background image
bg_img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "camp_lake_background.png")
bg_img_base64 = ""
if os.path.exists(bg_img_path):
    try:
        bg_img_base64 = get_base64_of_bin_file(bg_img_path)
    except Exception:
        pass

# Custom Styling (Forest Green, Camp Badge, Parallax Background & Modern Vibe)
css_styles = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;600;700&display=swap');
    
    /* Global font override */
    html, body, [class*="css"], .stMarkdown, p, div, label {
        font-family: 'Quicksand', sans-serif !important;
    }
    
    /* Scoped high-contrast text color overrides for widgets inside the main panel only */
    .block-container .stRadio label,
    .block-container .stRadio p,
    .block-container .stFileUploader label,
    .block-container .stFileUploader p,
    .block-container [data-testid="stFileUploadDropzone"] small,
    .block-container [data-testid="stFileUploadDropzone"] span {
        color: #2D312E !important;
    }
    .block-container [data-testid="stFileUploadDropzone"] button span {
        color: #FFFFFF !important;
    }
    
    /* Background with parallax effect and soft warm sand fade overlay */
    [data-testid='stAppViewContainer'] {
        background-image: linear-gradient(rgba(253, 251, 247, 0.88), rgba(253, 251, 247, 0.88)), url('data:image/png;base64,{bg_img_base64}');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
    }
    
    /* Make content block stand out slightly with a clean translucent layer */
    [data-testid="stAppViewBlockContainer"] {
        background-color: rgba(255, 255, 255, 0.02);
        border-radius: 24px;
        padding: 3rem !important;
        margin-top: 1rem;
    }
    
    /* Header layout */
    .header-container {
        background: linear-gradient(135deg, rgba(27, 67, 50, 0.95) 0%, rgba(45, 106, 79, 0.95) 100%);
        backdrop-filter: blur(8px);
        padding: 3rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 12px 40px rgba(27, 67, 50, 0.25);
        position: relative;
        overflow: hidden;
        border: 2px solid #2D6A4F;
    }
    .header-container::after {
        content: "🌲🏕️🌲";
        position: absolute;
        bottom: 0.5rem;
        right: 2rem;
        font-size: 4rem;
        opacity: 0.12;
    }
    .main-title {
        color: #FFFFFF !important;
        font-weight: 700;
        font-size: 3rem;
        margin: 0;
        letter-spacing: -0.5px;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .sub-title {
        color: #D8F3DC !important;
        font-size: 1.25rem;
        margin-top: 0.8rem;
        margin-bottom: 0;
        font-weight: 500;
        opacity: 0.95;
    }
    
    /* Glowing/spinning micro-animations */
    @keyframes pulse {
        0% { transform: scale(1); filter: drop-shadow(0 0 2px #E9C46A); }
        50% { transform: scale(1.15); filter: drop-shadow(0 0 12px #F77F00); }
        100% { transform: scale(1); filter: drop-shadow(0 0 2px #E9C46A); }
    }
    .camp-fire-glow {
        display: inline-block;
        animation: pulse 1.5s infinite ease-in-out;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .compass-spin {
        display: inline-block;
        animation: spin 10s infinite linear;
    }
    
    /* Modern buttons styled like outdoor gear badges */
    .stButton>button {
        background-color: #E9C46A;
        color: #1B4332 !important;
        border-radius: 30px;
        border: 2px solid #E9C46A;
        padding: 0.7rem 2.5rem;
        font-weight: 700;
        font-size: 1.1rem;
        letter-spacing: 0.5px;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        box-shadow: 0 4px 15px rgba(233, 196, 106, 0.25);
    }
    .stButton>button:hover {
        background-color: #1B4332;
        color: #E9C46A !important;
        border: 2px solid #E9C46A;
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 8px 25px rgba(27, 67, 50, 0.35);
    }
    
    /* Sidebar styled as deep green semi-transparent glass panel */
    [data-testid="stSidebar"] {
        background-color: rgba(27, 67, 50, 0.96) !important;
        backdrop-filter: blur(12px);
        border-right: 2px solid #2D6A4F;
    }
    [data-testid="stSidebar"] div, [data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] small {
        color: #D8F3DC !important;
    }
    [data-testid="stSidebar"] .sidebar-title {
        color: #E9C46A !important;
        border-bottom: 2px solid #2D6A4F;
        padding-bottom: 0.5rem;
    }
    [data-testid="stSidebar"] button {
        background-color: #E9C46A !important;
        color: #1B4332 !important;
        border: 2px solid #E9C46A !important;
    }
    [data-testid="stSidebar"] button:hover {
        background-color: #2D6A4F !important;
        color: #FFFFFF !important;
        border: 2px solid #FFFFFF !important;
    }
    [data-testid="stSidebar"] input {
        background-color: rgba(255, 255, 255, 0.08) !important;
        color: #FFFFFF !important;
        border: 1px solid #2D6A4F !important;
        border-radius: 8px;
    }
    [data-testid="stSidebar"] input:focus {
        border-color: #E9C46A !important;
        box-shadow: 0 0 0 1px #E9C46A !important;
    }
    
    /* Info Card styled like a classic camp wooden sign or trail guide */
    .info-card {
        background-color: rgba(244, 241, 234, 0.94) !important;
        backdrop-filter: blur(8px);
        color: #2D312E !important;
        padding: 1.8rem;
        border-radius: 16px;
        border-left: 8px solid #D08C60; /* Warm wood leather accent */
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .info-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.08);
    }
    .info-card strong {
        color: #1B4332;
        font-size: 1.25rem;
        display: block;
        margin-bottom: 0.8rem;
    }
    .info-card ol, .info-card li {
        color: #3D403E !important;
        font-size: 1.05rem;
        line-height: 1.6;
    }
    
    /* File uploader styling */
    [data-testid="stFileUploadDropzone"] {
        border: 2px dashed #2D6A4F !important;
        background-color: rgba(248, 249, 250, 0.85);
        backdrop-filter: blur(6px);
        border-radius: 16px;
        transition: background-color 0.3s ease, border-color 0.3s ease;
        padding: 2.5rem 1rem !important;
    }
    [data-testid="stFileUploadDropzone"]:hover {
        background-color: rgba(232, 245, 233, 0.9);
        border-color: #1B4332 !important;
    }
    
    /* Premium log card designs */
    .success-log-card {
        background-color: rgba(232, 245, 233, 0.92) !important;
        backdrop-filter: blur(8px);
        border-left: 6px solid #2D6A4F;
        padding: 1.2rem;
        border-radius: 12px;
        margin-bottom: 0.8rem;
        box-shadow: 0 4px 15px rgba(45, 106, 79, 0.08);
        transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
    }
    .success-log-card:hover {
        transform: translateX(6px) scale(1.005);
        box-shadow: 0 6px 18px rgba(45, 106, 79, 0.12);
    }
    .error-log-card {
        background-color: rgba(255, 235, 235, 0.92) !important;
        backdrop-filter: blur(8px);
        border-left: 6px solid #C62828;
        padding: 1.2rem;
        border-radius: 12px;
        margin-bottom: 0.8rem;
        box-shadow: 0 4px 15px rgba(198, 40, 40, 0.08);
        transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
    }
    .error-log-card:hover {
        transform: translateX(6px) scale(1.005);
        box-shadow: 0 6px 18px rgba(198, 40, 40, 0.12);
    }
    .log-title {
        font-weight: 700;
        font-size: 1.15rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .success-log-card .log-title {
        color: #1B4332;
    }
    .error-log-card .log-title {
        color: #C62828;
    }
    .log-meta {
        font-size: 0.95rem;
        color: #4A4A4A;
        display: flex;
        flex-wrap: wrap;
        gap: 1.5rem;
    }
    .log-badge {
        background-color: rgba(27, 67, 50, 0.08);
        color: #1B4332;
        padding: 0.15rem 0.6rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .error-log-card .log-badge {
        background-color: rgba(198, 40, 40, 0.08);
        color: #C62828;
    }
    
    /* Table headers matching woodsy palette */
    thead tr th {
        background-color: #1B4332 !important;
        color: white !important;
        font-weight: 700 !important;
    }
    
    /* Hide Streamlit Deploy button, MainMenu, footer and header decoration */
    .stAppDeployButton {
        display: none !important;
    }
    #MainMenu {
        display: none !important;
    }
    footer {
        display: none !important;
    }
    [data-testid="stDecoration"] {
        display: none !important;
    }
    </style>
""".replace("{bg_img_base64}", bg_img_base64)

st.markdown(css_styles, unsafe_allow_html=True)

# Path to local credentials storage
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "azure_config.json")

def load_config():
    """Loads config from a local JSON file if it exists."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"api_provider": "Standard OpenAI (Direct)", "api_key": "", "endpoint": "", "deployment": "gpt-4o-mini", "api_version": "2024-08-01-preview"}

def save_config(api_provider, api_key, endpoint, deployment, api_version):
    """Saves credentials to a local JSON file."""
    config = {
        "api_provider": api_provider,
        "api_key": api_key,
        "endpoint": endpoint,
        "deployment": deployment,
        "api_version": api_version
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

# Load existing configurations
config = load_config()

# ----------------- SIDEBAR -----------------
with st.sidebar:
    # Camp seal banner
    st.markdown("""
        <div style="text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #1B4332 0%, #2D6A4F 100%); border-radius: 16px; color: white; margin-bottom: 1.5rem; box-shadow: 0 4px 12px rgba(27,67,50,0.15);">
            <div class="compass-spin" style="font-size: 3rem;">🧭</div>
            <h3 style="margin-top: 0.5rem; color: #E9C46A; font-weight: 700; font-size: 1.25rem; letter-spacing: 0.5px; margin-bottom: 0;">CAMP BELKNAP</h3>
            <span style="font-size: 0.75rem; letter-spacing: 2px; color: #D8F3DC; text-transform: uppercase; font-weight: 600;">Est. 1903</span>
        </div>
    """, unsafe_allow_html=True)
    st.markdown('<p class="sidebar-title">⚙️ API Provider Settings</p>', unsafe_allow_html=True)
    st.write("Credentials are saved locally and do not need to be re-entered.")
    
    api_provider = st.radio(
        "API Provider", 
        ["Standard OpenAI (Direct)", "Azure OpenAI"], 
        index=0 if config.get("api_provider", "Standard OpenAI (Direct)") == "Standard OpenAI (Direct)" else 1
    )
    
    if api_provider == "Standard OpenAI (Direct)":
        api_key_input = st.text_input("OpenAI API Key", value=config.get("api_key", ""), type="password", placeholder="sk-proj-...")
        deployment_input = st.text_input("Model Name", value=config.get("deployment", "gpt-4o-mini"), placeholder="gpt-4o-mini")
        endpoint_input = ""
        api_version_input = ""
    else:
        api_key_input = st.text_input("Azure API Key", value=config.get("api_key", ""), type="password")
        endpoint_input = st.text_input("Azure Endpoint", value=config.get("endpoint", ""), placeholder="https://your-resource.openai.azure.com/")
        deployment_input = st.text_input("Deployment Name", value=config.get("deployment", ""), placeholder="gpt-4o-mini")
        api_version_input = st.text_input("API Version", value=config.get("api_version", "2024-08-01-preview"))
    
    if st.button("Save Settings"):
        save_config(api_provider, api_key_input, endpoint_input, deployment_input, api_version_input)
        st.success("Settings saved successfully!")
        st.rerun()

# ----------------- MAIN INTERFACE -----------------
st.markdown("""
<div class="header-container">
    <h1 class="main-title"><span class="compass-spin">🧭</span> Camp Belknap - Survey Tool <span class="camp-fire-glow">🔥</span></h1>
    <p class="sub-title">Extract handwritten survey results from scanned PDFs directly to a CSV using Azure AI</p>
</div>
""", unsafe_allow_html=True)

# Warning if settings are incomplete
settings_incomplete = not api_key_input or (api_provider == "Azure OpenAI" and (not endpoint_input or not deployment_input))

if settings_incomplete:
    st.warning("⚠️ Please fill in and save your API Provider Settings in the left sidebar to enable survey processing.")

# Step-by-step instructions
st.markdown("""
<div class="info-card">
    <strong>How to use this tool:</strong>
    <ol style="margin-top: 0.5rem; margin-bottom: 0;">
        <li>Make sure your Azure OpenAI settings are entered and saved in the sidebar.</li>
        <li>Drag and drop your scanned survey PDF file into the uploader below.</li>
        <li>Click <strong>"Start Survey Processing"</strong> and watch the results extract in real-time.</li>
        <li>Review the data table preview and download your CSV.</li>
    </ol>
</div>
""", unsafe_allow_html=True)

# Survey Type Selector
survey_type = st.radio(
    "Select Survey Type to Process",
    ["2026 Camper Survey", "2026 Leader Survey"],
    horizontal=True
)

# File uploader
uploaded_file = st.file_uploader("Upload Scanned Surveys PDF (Each survey must be exactly 2 pages)", type=["pdf"])

if uploaded_file is not None:
    try:
        # Load PDF document from bytes
        pdf_bytes = uploaded_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)
        
        st.info(f"📄 Successfully loaded **{uploaded_file.name}** ({total_pages} pages found). This contains approximately **{total_pages // 2} surveys**.")
        
        # Enable process button only if settings are complete
        if st.button("Start Survey Processing", disabled=settings_incomplete):
            # Resolve output path
            script_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(script_dir)
            output_dir = os.path.join(parent_dir, "SurveyOutput")
            os.makedirs(output_dir, exist_ok=True)
            output_csv_path = os.path.join(output_dir, "survey_results.csv")
            
            from openai import OpenAI, AzureOpenAI
            
            if api_provider == "Azure OpenAI":
                from urllib.parse import urlparse, parse_qs
                # Automatically clean endpoint URL if they pasted the full endpoint path
                cleaned_endpoint = endpoint_input.strip()
                parsed = urlparse(cleaned_endpoint)
                
                # Default to the user's API version input
                resolved_api_version = api_version_input.strip()
                
                # Extract api-version from query parameters if present
                if parsed.query:
                    query_params = parse_qs(parsed.query)
                    if "api-version" in query_params:
                        # Use the one from the URL if the user's input is empty or the default
                        url_api_version = query_params["api-version"][0]
                        if not resolved_api_version or resolved_api_version == "2024-08-01-preview":
                            resolved_api_version = url_api_version
                
                if parsed.scheme and parsed.netloc:
                    cleaned_endpoint = f"{parsed.scheme}://{parsed.netloc}/"
                    
                # Initialize Azure OpenAI Client
                client = AzureOpenAI(
                    api_key=api_key_input,
                    api_version=resolved_api_version,
                    azure_endpoint=cleaned_endpoint
                )
                model_name = deployment_input.strip()
            else:
                # Initialize standard OpenAI Client
                client = OpenAI(api_key=api_key_input.strip())
                model_name = deployment_input.strip() or "gpt-4o-mini"
            
            # Resolve schema class
            schema_class = LeaderSurvey2026 if survey_type == "Leader Survey 2026" else CamperSurvey2026
            
            results = []
            chunk_size = 2
            total_surveys = (total_pages + 1) // chunk_size
            
            # Layout elements for live progress tracking
            progress_bar = st.progress(0.0)
            status_text = st.empty()
            log_container = st.container()
            
            with log_container:
                st.write("### Live Extraction Logs:")
                
            for i in range(0, total_pages, chunk_size):
                survey_num = (i // chunk_size) + 1
                start_page = i + 1
                end_page = min(i + chunk_size, total_pages)
                
                # Update status
                status_text.markdown(f"**Processing Survey {survey_num} of {total_surveys}...**")
                
                # Convert PDF pages to base64 images
                try:
                    base64_images = get_survey_images_base64(doc, start_page, end_page)
                except Exception as e:
                    with log_container:
                        st.markdown(f"""
                        <div class="error-log-card">
                            <div class="log-title">❌ Survey #{survey_num} Image Conversion Failed</div>
                            <div class="log-meta">
                                <span>Failed to render pages {start_page}-{end_page}. Error: {e}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    continue
                
                # Call OpenAI/Azure OpenAI
                survey_data = process_survey_chunk(
                    client=client,
                    deployment_name=model_name,
                    base64_images=base64_images,
                    survey_num=survey_num,
                    start_page=start_page,
                    end_page=end_page,
                    schema_class=schema_class
                )
                
                if survey_data:
                    results.append(survey_data.model_dump())
                    name_str = getattr(survey_data, 'camper_name', None) or getattr(survey_data, 'leader_name', 'Anonymous')
                    cabin_str = getattr(survey_data, 'cabin', 'N/A')
                    div_str = getattr(survey_data, 'division', 'N/A')
                    with log_container:
                        st.markdown(f"""
                        <div class="success-log-card">
                            <div class="log-title">🌲 Survey #{survey_num}: {name_str}</div>
                            <div class="log-meta">
                                <span class="log-badge">Cabin {cabin_str}</span>
                                <span class="log-badge">{div_str} Division</span>
                                <span>Pages {start_page}-{end_page} successfully parsed</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    with log_container:
                        st.markdown(f"""
                        <div class="error-log-card">
                            <div class="log-title">❌ Survey #{survey_num}: Extraction Failed</div>
                            <div class="log-meta">
                                <span>Failed to parse handwritten OCR on pages {start_page}-{end_page}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Update progress bar
                progress_bar.progress(float(survey_num) / total_surveys)
                
            status_text.success(f"🎉 Processing complete! Successfully extracted {len(results)} of {total_surveys} surveys.")
            
            if results:
                # Compile to DataFrame
                df = pd.DataFrame(results)
                
                # Reorder columns slightly to keep info first
                if survey_type == "Leader Survey 2026":
                    info_cols = ['leader_name', 'division', 'cabin']
                else:
                    info_cols = ['division', 'cabin']
                
                info_cols = [col for col in info_cols if col in df.columns]
                other_cols = [col for col in df.columns if col not in info_cols]
                df = df[info_cols + other_cols]
                
                # Automatically save to SurveyOutput folder
                df.to_csv(output_csv_path, index=False)
                
                # Present interactive data preview table
                st.write("---")
                st.write("### Data Preview")
                st.dataframe(df, use_container_width=True)
                
                # Direct download button in browser
                csv_bytes = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download CSV File",
                    data=csv_bytes,
                    file_name="survey_results.csv",
                    mime="text/csv"
                )
                
                st.success(f"CSV copy also saved to: `{output_csv_path}`")
            else:
                st.error("No survey data was successfully extracted. CSV could not be generated.")
                
    except Exception as e:
        st.error(f"Failed to parse PDF file: {e}")
