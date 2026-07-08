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
class CampSurvey(BaseModel):
    camper_name: str = Field(description="The name of the camper, handwritten at the top of the first page. E.g. 'Grant Braasch'")
    division: str = Field(description="The division name, handwritten at the top of the first page. E.g. 'Juniors'")
    cabin: str = Field(description="The cabin letter or number, handwritten at the top of the first page. E.g. 'H' or 'J-H'")
    
    # Q1-Q3 Experience ratings (1-5)
    q1_cabin_rating: Optional[int] = Field(description="Cabin rating (circle 1-5, where 1 is terrible, 3 is ok, 5 is awesome)")
    q2_division_rating: Optional[int] = Field(description="Division rating (circle 1-5, where 1 is terrible, 3 is ok, 5 is awesome)")
    q3_camp_rating: Optional[int] = Field(description="Whole camp rating (circle 1-5, where 1 is terrible, 3 is ok, 5 is awesome)")
    
    # Q4 Session Days Rating (1-11, where 1 is favorite and 11 is least favorite, or 'NA' if written)
    q4_monday: Optional[str] = Field(description="Rating for Monday (1-11, or 'NA' if written/empty)")
    q4_tuesday: Optional[str] = Field(description="Rating for Tuesday (1-11, or 'NA' if written/empty)")
    q4_wednesday: Optional[str] = Field(description="Rating for Wednesday (1-11, or 'NA' if written/empty)")
    q4_thursday: Optional[str] = Field(description="Rating for Thursday (1-11, or 'NA' if written/empty)")
    q4_friday: Optional[str] = Field(description="Rating for Friday (1-11, or 'NA' if written/empty)")
    q4_saturday: Optional[str] = Field(description="Rating for Saturday (1-11, or 'NA' if written/empty)")
    q4_sunday: Optional[str] = Field(description="Rating for Sunday (1-11, or 'NA' if written/empty)")
    q4_2nd_monday: Optional[str] = Field(description="Rating for 2nd Monday (1-11, or 'NA' if written/empty)")
    q4_2nd_tuesday: Optional[str] = Field(description="Rating for 2nd Tuesday (1-11, or 'NA' if written/empty)")
    q4_2nd_wednesday: Optional[str] = Field(description="Rating for 2nd Wednesday (1-11, or 'NA' if written/empty)")
    q4_2nd_thursday: Optional[str] = Field(description="Rating for 2nd Thursday (1-11, or 'NA' if written/empty)")
    
    # Q5 Favorite Part of the Day
    q5_favorite_part_of_day: Optional[str] = Field(description="Favorite part of the day (Circle your answer: Meals, General Swim, Free Time in Divisions, Program Periods, Siesta, Evening Activities, Vespers)")
    
    # Q6 Play club/varsity sport
    q6_plays_sport: Optional[str] = Field(description="Do you play a club sport or varsity sport? (Yes or No)")
    
    # Q7 Play that sport while at camp
    q7_plays_sport_at_camp: Optional[str] = Field(description="Did you play that sport while at camp? (Yes or No)")
    
    # Q8 What camp activities were your favorite?
    q8_favorite_camp_activities: List[str] = Field(default_factory=list, description="List of camp activities circled/selected as favorites in Question 8. Look for circled/marked items on the page, which are listed in columns, e.g., Baseball, Low Ropes, Street Hockey, Adams' Cup, Soccer, Archery, Basketball, tennis, Woodshop, Nature, Crafts, Swimming, Windsurfing, Sailing, etc.")
    
    # Q9 How many new activities did you try?
    q9_new_activities_tried: Optional[int] = Field(description="How many new activities did you try? (Circle 0-10)")
    
    # Q10 Did you go to an activity that you weren't the best at yet?
    q10_tried_activity_not_best_at: Optional[str] = Field(description="Did you go to an activity that you weren't the best at yet? (Yes or No)")
    
    # Q11-Q16 Ratings (1-5, where 1 is Not at all, 5 is Very/A lot)
    q11_inclusion_rating: Optional[int] = Field(description="How included did you feel in activities? (Rating 1-5)")
    q12_new_friends_met: Optional[str] = Field(description="How many new friends did you meet at camp this summer? (Circle 1, 2, 3, 4, 5+)")
    q13_campers_listening_rating: Optional[int] = Field(description="How much did other campers listen to your ideas and opinions? (Rating 1-5)")
    q14_cabin_leader_comfort: Optional[int] = Field(description="How comfortable did you feel talking to your cabin leader? (Rating 1-5)")
    q15_return_next_summer: Optional[int] = Field(description="How interested are you in coming back to camp next summer? (Rating 1-5)")
    q16_recommend_camp: Optional[int] = Field(description="How likely are you to recommend Camp Belknap to someone else? (Rating 1-5)")
    
    # Q17 Comments
    q17_additional_comments: Optional[str] = Field(description="What else would like us to know about your camp experience? Transcribe the handwritten response exactly.")


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
    client: AzureOpenAI,
    deployment_name: str,
    base64_images: List[str],
    survey_num: int,
    start_page: int,
    end_page: int,
    retries: int = 3
) -> Optional[CampSurvey]:
    """Sends 2 survey page images to Azure OpenAI GPT-4o-mini and parses the structured response."""
    prompt = (
        "You are an expert OCR and survey processing AI. Analyze these 2 survey page images, which are scans of a Camper Survey for Camp Belknap.\n"
        "Carefully extract the camper's handwritten and circled answers for each question:\n"
        "- Look for circled numbers, circled words, checked boxes, and handwritten numbers in tables.\n"
        "- For questions with circular selections (like ratings 1-5 or yes/no): extract the circled/marked number or text. Refer to the schema field constraints to ensure selections correspond only to the allowed options.\n"
        "- For question 4 (rating table), read the handwritten numbers (1-11) or 'NA' for each day. Pay close attention to handwriting.\n"
        "- For question 8 (favorite activities), list all activities that have been circled or marked (the options are listed in columns, e.g., Baseball, Low Ropes, Street Hockey).\n"
        "- For question 17 (additional comments), transcribe the handwritten comment exactly as written. If they wrote 'Nothing' or 'N/A', transcribe that. If blank, return null.\n"
        "- If a question was not answered or is completely empty, leave it null.\n"
        "- Ensure the output strictly conforms to the allowed options and constraints in the requested JSON schema."
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
                response_format=CampSurvey,
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
            
        # Process using Azure OpenAI
        survey_data = process_survey_chunk(client, model_name, base64_images, survey_num, start_page, end_page)
        
        if survey_data:
            results.append(survey_data.model_dump())
            print(f"  Successfully extracted: {survey_data.camper_name} (Cabin {survey_data.cabin})")
        else:
            failures.append(survey_num)
            
    # Export results to CSV if we got any data
    if results:
        df = pd.DataFrame(results)
        
        # Reorder columns slightly to keep camper info first
        info_cols = ['camper_name', 'division', 'cabin']
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
