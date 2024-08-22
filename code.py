import os
import time
import google.generativeai as genai

# Set your API key directly in the code for now
genai.configure(api_key="AIzaSyA0Jx5lovrPEfz7_4_fLFwP4vttlOuRmXc")

def upload_to_gemini(path, mime_type=None):
    """Uploads the given file to Gemini."""
    file = genai.upload_file(path, mime_type=mime_type)
    print(f"Uploaded file '{file.display_name}' as: {file.uri}")
    return file

def wait_for_files_active(files):
    """Waits for the given files to be active."""
    print("Waiting for file processing...")
    for name in (file.name for file in files):
        file = genai.get_file(name)
        while file.state.name == "PROCESSING":
            print(".", end="", flush=True)
            time.sleep(10)
            file = genai.get_file(name)
        if file.state.name != "ACTIVE":
            raise Exception(f"File {file.name} failed to process")
    print("...all files ready\n")

# Configure the model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction="""You will be provided with natural language input and a database schema and also some files that contain values for some columns.
    SCHEMA:
    company_registration_number_1 (this is a flag that tells if company registration number is present or not)
    website_1 (this is a flag that tells if website is present or not)
    linkedin_1 (this is a flag that tells if linkedin is present or not)
    facebook_1 (this is a flag that tells if facebook is present or not)
    twitter_1 (this is a flag that tells if twitter is present or not)
    instagram_1 (this is a flag that tells instagram is present or not)
    employees (this tells the employee size)
    turnover (this tells the turnover value for the company)
    company_age (this tells the age of the company)
    SIC_code (SIC code)
    sector
    industry
    sub_industry
    country
    Post_Town
    Post_Code
    exclude_flag (which basically tells if the column is valid or not)
    Your task is to generate an accurate SQL query to retrieve relevant data from the table based on the input. 
    Begin by analyzing the input to identify the required data and context, then match the identified values or attributes to the corresponding schema columns. 
    Refer to the provided files for column values; if an exact match is found, use it in the SQL query, otherwise use the most relevant columns or values based on context and similarity.
    Specifically, when dealing with industry, sub-industry, or sector, first check for direct matches in the sector column; if no match is found, check the industry column, followed by the sub-industry column, ensuring each term in the user query is matched to its respective column according to this hierarchy. 
    Even if you find multiple sectors or industries or sub-industries, give them all. 
    For SIC codes, check the description provided and return the SIC code that matches the requirements. 
    Ensure the resulting SQL query accurately reflects the values present in the original table, using the correct column names for the corresponding values.
    For example, if the input is 'Give me construction companies,' first look at the sector column for the closest match; if none is found, move to the industry column, and if still no match, check the sub-industry column, ensuring the SQL query includes the correct column name for the matching value.
    Do not give any description, give only the query.
    Consider that all the files are from a single table "your_table."
    You should not assume any sub-industry, industry, or sector. It must be from the data that is given.
    I want you to add "exclude_flag=0" as a basic condition in every query you generate.
    """
)

# Provide the full path to your files
files = [
    upload_to_gemini(r"sic table ch.csv", mime_type="text/csv"),
    upload_to_gemini(r"ssisample.csv", mime_type="text/csv"),
    upload_to_gemini(r"locationsample.csv", mime_type="text/csv"),
]

# Wait for the files to be ready
wait_for_files_active(files)

# Start the chat session with the model
chat_session = model.start_chat(
    history=[
        {
            "role": "user",
            "parts": [
                files[0],
                files[1],
                files[2],
                "i need advertising companies with more than 100 employees",
            ],
        },
        {
            "role": "model",
            "parts": [
                "```sql\nSELECT * FROM your_table WHERE industry = 'Advertising Services' AND employees > 100 AND exclude_flag = 0;\n```",
            ],
        },
        # Add more conversation history as needed
    ]
)

# Send a new message
response = chat_session.send_message("INSERT_INPUT_HERE")

# Print the response (SQL Query)
print(response.text)
