import streamlit as str
import google.generativeai as genai
import pandas as pd
import json
import io
from PIL import Image

# 1. Setup Streamlit Page Configuration
str.set_page_config(page_title="Paper Sheet to Excel Converter", layout="centered")
str.title("📄 Paper Sheet to Excel Converter")
str.write("Upload a photo or scan of a data sheet, and AI will convert it into a downloadable Excel file.")

# 2. API Key Configuration
# Securely input your Gemini API key (Get one from Google AI Studio)
api_key = str.sidebar.text_input("Enter Google Gemini API Key:", type="password")

if not api_key:
    str.info("Please enter your Gemini API key in the sidebar to get started.", icon="🔑")
    str.stop()

# Initialize the Gemini Client
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

# 3. File Uploader Interface
uploaded_file = str.file_uploader("Choose a scanned image or photo...", type=["jpg", "jpeg", "png", "webp"])

if uploaded_file is not None:
    # Display the uploaded image
    image = Image.open(uploaded_file)
    str.image(image, caption="Uploaded Data Sheet", use_container_width=True)
    
    # Process Button
    if str.button("🚀 Extract Data to Excel"):
        with str.spinner("AI is reading the data sheet and structuring the table..."):
            try:
                # System prompt forcing the AI to return data ONLY as a clean JSON array of objects
                prompt = (
                    "Analyze this scanned data sheet image. Extract all tabular data into a structured format. "
                    "Return the data strictly as a valid JSON array of objects, where each object represents a row. "
                    "Use the table headers as the keys for the JSON objects. Do not include markdown code blocks, "
                    "do not include ```json tags, and do not provide any introductory or concluding text. Just valid JSON."
                )
                
                # Call Gemini API with the image and prompt
                response = model.generate_content([prompt, image])
                raw_text = response.text.strip()
                
                # Clean up potential markdown formatting if the model ignored instructions
                if raw_text.startswith("```"):
                    raw_text = raw_text.split("\n", 1)[1]
                if raw_text.endswith("```"):
                    raw_text = raw_text.rsplit("\n", 1)[0]
                if raw_text.startswith("json"):
                    raw_text = raw_text.split("json", 1)[1]
                
                raw_text = raw_text.strip()
                
                # Parse JSON string into Python Data
                data_json = json.loads(raw_text)
                
                # Convert to Pandas DataFrame
                df = pd.DataFrame(data_json)
                
                # Display extracted data in the browser
                str.success("🎉 Data extracted successfully!")
                str.subheader("Preview of Extracted Data")
                str.dataframe(df)
                
                # Convert DataFrame to an Excel file buffer in memory
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name="Extracted Data")
                excel_data = excel_buffer.getvalue()
                
                # Download Button for the Excel sheet
                str.download_button(
                    label="📥 Download Excel File",
                    data=excel_data,
                    file_name="extracted_data_sheet.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
            except json.JSONDecodeError:
                str.error("Failed to parse the AI output into a table. The scan might be too blurry or complex.")
                str.text_area("Raw AI Response for Debugging:", response.text)
            except Exception as e:
                str.error(f"An error occurred: {str(e)}")
