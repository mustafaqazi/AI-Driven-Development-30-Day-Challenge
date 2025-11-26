import os
import io
import json
import dotenv
import google.generativeai as genai
from pypdf import PdfReader

dotenv.load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file. Please set it.")

genai.configure(api_key=GEMINI_API_KEY)

class StudyAgent:
    def __init__(self, model_name='gemini-2.5-flash'): # Using gemini-pro for text generation as per common practice, flash is good for chat
        self.model = genai.GenerativeModel(model_name)

    def extract_text_from_pdf(self, pdf_file_path):
        """
        Extracts text from a PDF file.
        Expects a file path or a file-like object.
        """
        try:
            if isinstance(pdf_file_path, str): # Path to file
                reader = PdfReader(pdf_file_path)
            elif hasattr(pdf_file_path, 'read'): # File-like object (e.g., from st.uploaded_file)
                reader = PdfReader(io.BytesIO(pdf_file_path.read()))
            else:
                raise TypeError("pdf_file_path must be a string path or a file-like object.")

            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return None

    def summarize_text(self, text, style="academic"):
        """
        Generates a summary of the provided text using the Gemini model.
        """
        prompt = f"""You are an expert study notes summarizer. Summarize the following PDF text in {style} style. Focus on key concepts, examples, and important details. Use headings, bullet points, or numbered lists. Avoid placeholder text. Return only the summary text.
        PDF Text:
        {text}
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error generating summary: {e}")
            return None

    def generate_quiz(self, pdf_text):
        """
        Generates quiz questions (MCQ, True/False, Fill-in-the-Blank) from the given text
        using the Gemini model and returns them in a structured JSON format.
        """
        # Using a more detailed prompt to ensure structured JSON output
        prompt = f"""
        You are an expert quiz generator. Based on the following study material, create a comprehensive quiz.
        The quiz should contain:
        1.  **10 Multiple Choice Questions (MCQs)**: Each MCQ should have 4 options (A, B, C, D) and a single correct answer.
        2.  **5 True/False Questions**: Each question should have 'True' or 'False' as the correct answer.
        3.  **5 Fill-in-the-Blank Questions**: Each question should have exactly one blank represented by '_______' and a single correct answer for the blank.

        Format the entire quiz as a JSON object with two top-level keys: "mcqs" (a list of MCQ objects) and "mixed_questions" (a list of mixed question objects).

        Each MCQ object must have:
        - "question": The question text.
        - "options": A list of 4 strings, e.g., ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"].
        - "correct_answer": The letter (A, B, C, or D) corresponding to the correct option.

        Each mixed question object must have:
        - "type": "true_false" or "fill_in_the_blank".
        - "question": The question text.
        - "correct_answer": The correct answer (e.g., "True", "False", or the word/phrase for fill-in-the-blank).

        Ensure the questions cover important concepts, definitions, and facts from the material.
        Do NOT include any introductory or concluding remarks, only the JSON output.

        Study Material:
        {pdf_text}
        """
        try:
            response = self.model.generate_content(prompt)
            # Gemini sometimes adds markdown ```json ... ``` wrapper
            quiz_json_str = response.text.strip()
            if quiz_json_str.startswith("```json"):
                quiz_json_str = quiz_json_str[len("```json"):
].strip()
            if quiz_json_str.endswith("```"):
                quiz_json_str = quiz_json_str[:-len("```")].strip()
                
            quiz_data = json.loads(quiz_json_str)
            
            # Basic validation of the quiz structure
            if "mcqs" not in quiz_data or "mixed_questions" not in quiz_data:
                raise ValueError("Quiz data missing 'mcqs' or 'mixed_questions' keys.")
            
            return quiz_data

        except json.JSONDecodeError as e:
            print(f"Error decoding quiz JSON from Gemini response: {e}")
            print(f"Raw response text: {response.text}")
            return None
        except Exception as e:
            print(f"Error generating quiz: {e}")
            return None

if __name__ == '__main__':
    # Example usage for testing agent functions
    agent = StudyAgent()

    # --- Test PDF Extraction (Requires a dummy PDF file) ---
    # Create a dummy PDF file for testing
    with open("dummy.pdf", "wb") as f:
        f.write(b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Contents 4 0 R/Parent 2 0 R/Resources<<>>>>endobj 4 0 obj<</Length 44>>stream\nBT /F1 24 Tf 100 700 Td (Hello, this is a test PDF!) Tj ET\nendstream\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000055 00000 n\n0000000130 00000 n\n0000000241 00000 n\ntrailer<</Size 5/Root 1 0 R>>startxref\n299\n%%EOF")

    print("\n--- Testing PDF Extraction ---")
    extracted_text = agent.extract_text_from_pdf("dummy.pdf")
    if extracted_text:
        print("Extracted Text:")
        print(extracted_text[:100] + "...") # Print first 100 chars
    else:
        print("PDF extraction failed.")
    os.remove("dummy.pdf") # Clean up dummy file

    # --- Test Summarization ---
    print("\n--- Testing Summarization ---")
    sample_text = "The quick brown fox jumps over the lazy dog. This is a common pangram used to display all letters of the alphabet. Pangrams are useful for typewriters and font designers."
    summary = agent.summarize_text(sample_text)
    if summary:
        print("Summary:")
        print(summary)
    else:
        print("Summarization failed.")

    # --- Test Quiz Generation ---
    print("\n--- Testing Quiz Generation ---")
    quiz_data = agent.generate_quiz(sample_text)
    if quiz_data:
        print("Generated Quiz:")
        print(json.dumps(quiz_data, indent=2))
    else:
        print("Quiz generation failed.")


