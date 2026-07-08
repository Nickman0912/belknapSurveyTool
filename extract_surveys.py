import os
import argparse
import json
import base64
import time
from typing import List, Optional
import pandas as pd
from pydantic import BaseModel, Field

# Check if required libraries are installed
try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: The 'pymupdf' package is not installed.")
    print("Please install it using: pip install -r requirements.txt")
    exit(1)

try:
    from openai import OpenAI, AzureOpenAI, RateLimitError
    from openai import APIError
except ImportError:
    print("Error: The 'openai' package is not installed.")
    print("Please install it using: pip install -r requirements.txt")
    exit(1)

# Define the Pydantic schema for the camper survey
class CamperSurvey2026(BaseModel):
    division: Optional[str] = Field(description="The division name at the top of the first page. E.g. 'Juniors'")
    cabin: Optional[str] = Field(description="The cabin letter or number at the top of the first page. E.g. 'H' or 'J-H'")
    
    # Q1-Q3 Experience ratings (1-5)
    q1_cabin_rating: Optional[int] = Field(description="Cabin rating (circle 1-5, where 1 is terrible, 3 is ok, 5 is awesome)")
    q2_division_rating: Optional[int] = Field(description="Division rating (circle 1-5, where 1 is terrible, 3 is ok, 5 is awesome)")
    q3_camp_rating: Optional[int] = Field(description="Whole camp rating (circle 1-5, where 1 is terrible, 3 is ok, 5 is awesome)")
    
    # Q4 Favorite Part of the Day
    q4_favorite_part_of_day: Optional[str] = Field(description="Favorite part of the day (Circle your answer: Meals, Vespers, Evening Activities, Program Periods, Siesta, General Swim, Free Time in Divisions)")
    
    # Q5 What camp activities were your favorite?
    q5_favorite_camp_activities: List[str] = Field(default_factory=list, description="List of camp activities circled/selected as favorites in Question 5.")
    
    # Q6 How many new activities did you try?
    q6_new_activities_tried: Optional[int] = Field(description="How many new activities did you try? (Circle 0-10)")
    
    # Q7 Do you play a club sport or varsity sport at home?
    q7_plays_sport_at_home: Optional[str] = Field(description="Do you play a club sport or varsity sport at home? (Circle Yes or No)")
    
    # Q8 Did you play that sport while at camp?
    q8_played_sport_at_camp: Optional[str] = Field(description="Did you play that sport while at camp? (Circle Yes or No)")
    
    # Q9 Did you go to an activity that you weren't the best at yet?
    q9_tried_activity_not_best_at: Optional[str] = Field(description="Did you go to an activity that you weren't the best at yet? (Circle Yes or No)")
    
    # Q10 How included did you feel in activities?
    q10_inclusion_rating: Optional[int] = Field(description="How included did you feel in activities? (Rating 1-5)")
    
    # Q11 How many new friends did you meet at camp this summer?
    q11_new_friends_met: Optional[str] = Field(description="How many new friends did you meet at camp this summer? (Circle 1, 2, 3, 4, 5+)")
    
    # Q12 How comfortable did you feel talking to your cabin leader?
    q12_cabin_leader_comfort: Optional[int] = Field(description="How comfortable did you feel talking to your cabin leader? (Rating 1-5)")
    
    # Q13 How interested are you in coming back to camp next summer?
    q13_return_next_summer: Optional[int] = Field(description="How interested are you in coming back to camp next summer? (Rating 1-5)")
    
    # Q14 How likely are you to recommend Camp Belknap to someone else?
    q14_recommend_camp: Optional[int] = Field(description="How likely are you to recommend Camp Belknap to someone else? (Rating 1-5)")
    
    # Q15 What else would you like us to know about your camp experience?
    q15_additional_comments: Optional[str] = Field(description="What else would you like us to know about your camp experience? Transcribe the handwritten response exactly.")


class LeaderSurvey2026(BaseModel):
    leader_name: Optional[str] = Field(description="The leader's name handwritten at the top of the first page.")
    division: Optional[str] = Field(description="The division name handwritten at the top of the first page. E.g. 'Juniors'")
    cabin: Optional[str] = Field(description="The cabin letter or number handwritten at the top of the first page. E.g. 'H' or 'J-H'")
    
    # Q1-Q3 Experience ratings (1-5)
    q1_cabin_rating: Optional[int] = Field(description="Cabin rating (circle 1-5, where 1 is terrible, 3 is ok, 5 is awesome)")
    q2_division_rating: Optional[int] = Field(description="Division rating (circle 1-5, where 1 is terrible, 3 is ok, 5 is awesome)")
    q3_camp_rating: Optional[int] = Field(description="Whole camp rating (circle 1-5, where 1 is terrible, 3 is ok, 5 is awesome)")
    
    # Q4 Rate your overall well-being during this session
    q4_well_being_rating: Optional[int] = Field(description="Overall well-being rating (circle 1-5, where 1 is terrible, 3 is ok, 5 is awesome)")
    
    # Q5 Were you able to be present, engaged, and focused during the session?
    q5_focus_rating: Optional[int] = Field(description="Ability to be present, engaged, and focused (circle 1-5, where 1 is Not at all, 3 is Some of the time, 5 is The whole time)")
    
    # Q6 Were there parts of this session that felt difficult (please explain)?
    q6_difficult_parts: Optional[str] = Field(description="Transcribe the printed explanation of what parts of the session felt difficult.")
    
    # Q7 What support or experiences made your job as a Belknap leader easier this session?
    q7_easier_support: Optional[str] = Field(description="Transcribe what support or experiences made their job as a leader easier.")
    
    # Q8 What was your favorite part of the day?
    q8_favorite_part_of_day: Optional[str] = Field(description="Favorite part of the day (Circle your answer: Meals, Program Periods, General Swim, Siesta, Vespers, Free time in Divs, Evening Activities)")
    
    # Q9 Campers who needed the most extra support
    q9_campers_needing_support: List[str] = Field(default_factory=list, description="List of names written under Question 9 (campers needing extra support).")
    
    # Q10 Campers ignored or not listened to by their peers
    q10_campers_ignored: List[str] = Field(default_factory=list, description="List of names written under Question 10 (campers ignored or not listened to by peers).")
    
    # Q11 Campers suggested to reach out to in the off season
    q11_campers_reach_out: List[str] = Field(default_factory=list, description="List of names written under Question 11 (campers to reach out to in off season).")
    
    # Q12 What else would you like the senior staff to know about your experience?
    q12_additional_comments: Optional[str] = Field(description="Transcribe the comments under Question 12 exactly.")
    
    # Q13 What do you think Belknap should do to increase the number of leaders who return each summer?
    q13_increase_returning_leaders: Optional[str] = Field(description="Transcribe the recommendations under Question 13 exactly.")


def get_survey_images_base64(doc: fitz.Document, start_page: int, end_page: int) -> List[str]:
    """Converts a range of PDF pages (0-indexed) to PNG base64 strings in memory."""
    base64_images = []
    # fitz pages are 0-indexed, so we subtract 1 from start_page and end_page
    for page_num in range(start_page - 1, min(end_page, len(doc))):
        page = doc.load_page(page_num)
        # 150 DPI is a good balance of OCR accuracy and file size
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        base64_str = base64.b64encode(img_bytes).decode("utf-8")
        base64_images.append(base64_str)
    return base64_images


def process_survey_chunk(
    client: OpenAI,
    deployment_name: str,
    base64_images: List[str],
    survey_num: int,
    start_page: int,
    end_page: int,
    schema_class: type,
    retries: int = 3
) -> Optional[BaseModel]:
    """Sends 2 survey page images to Azure OpenAI/OpenAI and parses the structured response."""
    if schema_class.__name__ == "LeaderSurvey2026":
        prompt = (
            "You are an expert OCR and survey processing AI. Analyze these 2 survey page images, which are scans of a Leader Survey (Summer 2026) for Camp Belknap.\n"
            "Carefully extract the leader's handwritten and circled answers for each question:\n"
            "- CRITICAL: Only extract answers that have been clearly circled, checked, or written by hand. Do not select or extract default printed options unless they have a handwritten circle, checkmark, or pen mark on/around them.\n"
            "- If a question or the entire page is completely blank/unmarked, you MUST set those fields to null (or an empty list for lists). Do not guess or hallucinate any answers.\n"
            "- Extract circled numbers, circled words, and handwritten comments/names exactly as written.\n"
            "- For questions 9, 10, and 11, extract the list of handwritten names (up to 3 names each).\n"
            "- Ensure the output conforms to the requested JSON schema structure."
        )
    else:
        prompt = (
            "You are an expert OCR and survey processing AI. Analyze these 2 survey page images, which are scans of a Camper Survey 2026 for Camp Belknap.\n"
            "Carefully extract the camper's handwritten and circled answers for each question:\n"
            "- CRITICAL: Only extract answers that have been clearly circled, checked, or written by hand. Do not select or extract default printed options unless they have a handwritten circle, checkmark, or pen mark on/around them.\n"
            "- If a question or the entire page is completely blank/unmarked, you MUST set those fields to null (or an empty list for lists). Do not guess or hallucinate any answers.\n"
            "- Extract circled numbers, circled words, and handwritten comments exactly as marked.\n"
            "- Ensure the output conforms to the requested JSON schema structure."
        )
    
    # Construct the multimodal user content
    content_list = [{"type": "text", "text": prompt}]
    for img_base64 in base64_images:
        content_list.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{img_base64}"
            }
        })
        
    messages = [
        {
            "role": "user",
            "content": content_list
        }
    ]
    
    for attempt in range(retries):
        try:
            print(f"Processing Survey #{survey_num} (PDF Pages {start_page}-{end_page})...")
            
            completion = client.beta.chat.completions.parse(
                model=deployment_name,
                messages=messages,
                response_format=schema_class,
                temperature=0.0,  # 0.0 temperature for deterministic extraction
            )
            
            return completion.choices[0].message.parsed
            
        except RateLimitError as e:
            print(f"  Rate limit hit on attempt {attempt+1}/{retries}. Waiting 25 seconds before retrying...")
            if attempt < retries - 1:
                time.sleep(25)
            else:
                print(f"  Failed to process Survey #{survey_num} after {retries} attempts due to Rate Limit.")
        except APIError as e:
            print(f"  API error on attempt {attempt+1}/{retries}: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"  Failed to process Survey #{survey_num} after {retries} attempts.")
        except Exception as e:
            print(f"  Unexpected error on attempt {attempt+1}/{retries}: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"  Failed to process Survey #{survey_num} after {retries} attempts.")
                
    return None


def main():
    # Resolve default output directory (BelknapDev/SurveyOutput) relative to the script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    default_output_dir = os.path.join(parent_dir, "SurveyOutput")
    default_output_path = os.path.join(default_output_dir, "survey_results.csv")

    parser = argparse.ArgumentParser(description="Extract Camp Belknap Camper Surveys using Azure OpenAI.")
    parser.add_argument("pdf_path", type=str, help="Path to the scanned multi-page survey PDF file.")
    parser.add_argument("-o", "--output", type=str, default=default_output_path, help=f"Path to save the output CSV (default: {default_output_path})")
    parser.add_argument("-t", "--type", type=str, choices=["camper", "leader"], default="camper", help="The survey type to extract (default: camper)")
    parser.add_argument("--endpoint", type=str, default=None, help="Azure OpenAI endpoint URL. If not provided, looks for AZURE_OPENAI_ENDPOINT env var.")
    parser.add_argument("--api-key", type=str, default=None, help="Azure OpenAI API Key. If not provided, looks for AZURE_OPENAI_API_KEY env var.")
    parser.add_argument("--deployment", type=str, default=None, help="Azure OpenAI model deployment name. If not provided, looks for AZURE_OPENAI_DEPLOYMENT_NAME env var.")
    parser.add_argument("--api-version", type=str, default="2024-08-01-preview", help="Azure OpenAI API version (default: 2024-08-01-preview)")
    args = parser.parse_args()
    
    from urllib.parse import urlparse, parse_qs

    # Resolve Credentials
    api_key = args.api_key or os.environ.get("AZURE_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    endpoint = args.endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT")
    deployment = args.deployment or os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")

    # Resolve API version (check if custom, fallback to query parameter, then fallback to argument)
    api_version = args.api_version

    # Determine if we are using Azure or standard OpenAI
    use_azure = endpoint is not None or os.environ.get("AZURE_OPENAI_ENDPOINT") is not None

    if use_azure:
        # Automatically clean endpoint URL if the user passed the full completions path
        if endpoint:
            endpoint = endpoint.strip()
            parsed = urlparse(endpoint)
            
            # Extract api-version from query parameters if present and using default/none
            if parsed.query:
                query_params = parse_qs(parsed.query)
                if "api-version" in query_params:
                    url_api_version = query_params["api-version"][0]
                    if not api_version or api_version == "2024-08-01-preview":
                        api_version = url_api_version
                        
            if parsed.scheme and parsed.netloc:
                endpoint = f"{parsed.scheme}://{parsed.netloc}/"
        
        missing_vars = []
        if not api_key:
            missing_vars.append("AZURE_OPENAI_API_KEY")
        if not endpoint:
            missing_vars.append("AZURE_OPENAI_ENDPOINT")
        if not deployment:
            missing_vars.append("AZURE_OPENAI_DEPLOYMENT_NAME")
            
        if missing_vars:
            print("Error: Missing Azure OpenAI credentials.")
            print(f"Please set the following environment variables or specify them as CLI arguments: {', '.join(missing_vars)}")
            print("\nTo set environment variables in Windows (PowerShell) for Azure:")
            print("  $env:AZURE_OPENAI_API_KEY=\"your_api_key\"")
            print("  $env:AZURE_OPENAI_ENDPOINT=\"https://your-resource.openai.azure.com/\"")
            print("  $env:AZURE_OPENAI_DEPLOYMENT_NAME=\"gpt-4o-mini\"")
            exit(1)
    else:
        if not api_key:
            print("Error: Missing OpenAI API credentials.")
            print("Please set the OPENAI_API_KEY environment variable or specify it via --api-key.")
            print("\nTo set standard OpenAI API Key in Windows (PowerShell):")
            print("  $env:OPENAI_API_KEY=\"sk-proj-...\"")
            exit(1)
        
    # Check if the PDF file exists
    if not os.path.exists(args.pdf_path):
        print(f"Error: The file '{args.pdf_path}' does not exist.")
        exit(1)
        
    # Open PDF
    try:
        doc = fitz.open(args.pdf_path)
        total_pages = len(doc)
        print(f"Successfully loaded PDF: {args.pdf_path} (Total pages: {total_pages})")
    except Exception as e:
        print(f"Error reading PDF file: {e}")
        exit(1)
        
    # Initialize client
    if use_azure:
        client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint
        )
        model_name = deployment
    else:
        client = OpenAI(api_key=api_key)
        model_name = deployment or "gpt-4o-mini"
    
    # Resolve schema class
    schema_class = LeaderSurvey2026 if args.type == "leader" else CamperSurvey2026
    
    results = []
    failures = []
    chunk_size = 2
    
    # Process PDF in 2-page chunks
    for i in range(0, total_pages, chunk_size):
        survey_num = (i // chunk_size) + 1
        start_page = i + 1
        end_page = min(i + chunk_size, total_pages)
        
        # Render pages to base64 images
        try:
            base64_images = get_survey_images_base64(doc, start_page, end_page)
        except Exception as e:
            print(f"Error rendering pages {start_page}-{end_page} to images: {e}")
            failures.append(survey_num)
            continue
            
        # Process using OpenAI/Azure OpenAI
        survey_data = process_survey_chunk(client, model_name, base64_images, survey_num, start_page, end_page, schema_class)
        
        if survey_data:
            results.append(survey_data.model_dump())
            name_str = getattr(survey_data, 'camper_name', None) or getattr(survey_data, 'leader_name', 'Anonymous')
            print(f"  Successfully extracted: {name_str} (Cabin {getattr(survey_data, 'cabin', 'N/A')})")
        else:
            failures.append(survey_num)
            
    # Export results to CSV if we got any data
    if results:
        df = pd.DataFrame(results)
        
        # Reorder columns slightly to keep info first
        if args.type == "leader":
            info_cols = ['leader_name', 'division', 'cabin']
        else:
            info_cols = ['division', 'cabin']
            
        info_cols = [col for col in info_cols if col in df.columns]
        other_cols = [col for col in df.columns if col not in info_cols]
        df = df[info_cols + other_cols]
        
        # Ensure the output directory exists
        output_dir = os.path.dirname(os.path.abspath(args.output))
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
        # Save to CSV
        df.to_csv(args.output, index=False)
        print("\n" + "="*50)
        print(f"Extraction Completed!")
        print(f"Successfully processed: {len(results)}/{((total_pages + 1) // chunk_size)} surveys.")
        if failures:
            print(f"Failed surveys: {failures}")
        print(f"Results saved to: {os.path.abspath(args.output)}")
        print("="*50)
    else:
        print("\nNo survey data was successfully extracted. CSV was not generated.")


if __name__ == "__main__":
    main()
