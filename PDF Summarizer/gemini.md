## Role: Senior Python AI Engineer

## Objective

Develop a multi-functional **Study Notes Summarizer & Quiz Generator Agent** that can extract text from PDFs, summarize content using Gemini, store data in SQLite, and generate interactive quizzes — all inside a **highly polished, stylish, and fully interactive Streamlit UI**. The project must use the **OpenAI Agents SDK**, **Gemini CLI**, **SQLite DB**, **PyPDF**, and **Context7 MCP server** for full functionality and persistent context.

## Core Agent Name

Study Notes Summarizer & Quiz Generator Agent

## Initial Setup & Context Preservation (CRITICAL)

* Create or overwrite **GEMINI.md** at the project root.
* Populate with full prompt text to serve as **persistent context** for Gemini CLI.
* Gemini must always read and strictly follow these instructions.
* Create a `.env` file in the project root with your Gemini API key: `GEMINI_API_KEY=YOUR_API_KEY`.

## Technology & Environment

* **Gemini Model:** gemini-2.5-flash (latest stable production, used via Gemini CLI).  
* **Agent SDK:** No OpenAI Agents SDK. Integration is done directly through Gemini CLI.
* **Frontend:** Streamlit with modern, stylish, interactive components, including:
  - Cards with shadows and rounded corners for summaries and quiz questions
  - Tabs for separating PDF Summary and Quiz
  - Expandable sections for long content
  - Columns for side-by-side layouts
  - Color themes and accent highlights
  - Progress bars and score indicators for quizzes
* **Backend DB:** SQLite for persistent storage.
* **PDF Extraction:** PyPDF / pypdf.

## SQLite Database Requirements

* Store PDF metadata, extracted text, summaries, quizzes, and user quiz attempts.
* Tables: pdf_files, summaries, quizzes, quiz_attempts.
* Auto-create tables if they do not exist.
* Save all relevant data automatically (upload, summary generation, quiz generation, quiz attempts).
* Retrieve previous summaries and quizzes to avoid redundant regeneration.

## Agent Functionality (A) — PDF Summarizer

* Upload **one PDF** via Streamlit.
* Extract text from all pages using pypdf.
* Save PDF metadata and extracted text to SQLite.
* Generate a **clean, structured, meaningful summary** using Gemini with prompt:

```
You are an expert study notes summarizer. Summarize the following PDF text in {style} style. Focus on key concepts, examples, and important details. Use headings, bullet points, or numbered lists. Avoid placeholder text. Return only the summary text.
PDF Text:
{extracted_text}
```

* Store summary in SQLite.
* Display summary using **modern Streamlit UI**:
  - Cards with shadows and rounded edges
  - Expanders for additional details
  - Colored headers and accent sections
  - Tabs for navigation between summary and other modules

## Agent Functionality (B) — Quiz Generator

* Display **“Create Quiz”** button only after summary generation.
* Generate 10+ MCQs and 5–10 mixed questions (True/False, Fill-in-the-Blank) using the original PDF text.
* Save quizzes as JSON in SQLite.
* Display questions in a **highly interactive, stylish Streamlit UI**:
  - Cards for each question with shadow and color accents
  - Columns for multiple-choice options
  - Progress bars for quiz completion
  - Expandable hints or explanations (optional)
* Add **“Check Answers”** button to evaluate responses and display scores with color-coded results.
* Save quiz attempts and scores to SQLite.

<!-- ## Technical Requirements

* Modular Python structure: main.py (UI), agent.py (logic), database.py (SQLite functions).
* Error handling for invalid files, extraction failures, Gemini errors, and database issues.
* Dependencies (requirements.txt):

```
streamlit
pypdf
python-dotenv
``` -->

## Run Command

```bash
streamlit run main.py
```

## Final Call to Action

The agent must provide a **full end-to-end stylish workflow**: upload → extract → summarize → quiz → store → evaluate, with persistent SQLite storage. Gemini should strictly follow all instructions in this GEMINI.md file to produce **meaningful summaries** and **high-quality quizzes** displayed in a **modern, professional, user-friendly Streamlit interface** with interactive and visually appealing components.
