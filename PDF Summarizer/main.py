import streamlit as st
import os
import json
import tempfile
from datetime import datetime
from database import connect_db, create_tables, insert_pdf_data, get_pdf_data, \
                     insert_summary, get_summary, insert_quiz, get_quiz, \
                     insert_quiz_attempt, get_pdf_data_by_id
from agent import StudyAgent 

# --- Configuration ---
conn = connect_db()
create_tables(conn)
conn.close()

# Initialize StudyAgent
study_agent = StudyAgent(model_name='gemini-2.5-flash')  # Using gemini-pro

# Streamlit page configuration
st.set_page_config(
    page_title="Study Notes Summarizer & Quiz Generator",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for modern and sleek UI ---
st.markdown("""
<style>
/* Main app background */
.stApp {
    background-color: #f9f9f9 !important;
    font-family: 'Segoe UI', sans-serif;
}

/* Headings */
h1, h2, h3, h4, h5, h6 {
    color: #2e3b4e !important;
    font-weight: bold !important;
}

/* Paragraphs */
p, div, span, label {
    color: #2e3b4e !important;
    font-size: 16px !important;
}

/* Cards */
.stCard {
    background-color: #ffffff !important;
    border-radius: 12px !important;
    box-shadow: 0 6px 12px rgba(0,0,0,0.1) !important;
    padding: 20px !important;
    margin-bottom: 20px !important;
    transition: transform 0.2s, box-shadow 0.2s;
}

.stCard:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0,0,0,0.15) !important;
}

/* Buttons */
.stButton>button {
    background-color: #4CAF50 !important;
    color: white !important;
    border-radius: 8px !important;
    border: none !important;
    padding: 10px 24px !important;
    font-size: 16px !important;
    font-weight: bold !important;
    cursor: pointer;
    transition: 0.3s;
}

.stButton>button:hover {
    background-color: #45a049 !important;
}

/* File uploader */
.stFileUploader section {
    border: 2px dashed #2e3b4e !important;
    border-radius: 10px !important;
    padding: 12px !important;
    background-color: #fdfdfd !important;
}

/* Sidebar */
.css-1d391kg {
    color: #ffffff !important;
    font-weight: 600 !important;
}

/* Tabs */
# .stTabs [data-baseweb="tab"] {
#     color: white !important;
#     font-weight: bold !important;
#     background-color: #eaeaea !important;
#     border-radius: 10px 10px 0 0 !important;
# }

# .stTabs [aria-selected="true"] {
#     background-color: #4CAF50 !important;
#     color: #ffffff !important;
# }

.stTabs [data-baseweb="tab"] {
    color: #2e3b4e !important;           /* Tab text color */
    font-weight: bold !important;        /* Bold text */
    background-color: #e0e0e0 !important; /* Light gray background */
    border-radius: 10px 10px 0 0 !important; /* Rounded top corners */
    padding: 8px 16px !important;       /* Padding inside tab */
    transition: 0.3s;                   /* Smooth hover transition */
}

/* Hover effect for tabs */
.stTabs [data-baseweb="tab"]:hover {
    background-color: #d4d4d4 !important; /* Slightly darker gray on hover */
}

/* Selected tab */
.stTabs [aria-selected="true"] {
    background-color: #4CAF50 !important; /* Green background for active tab */
    color: #ffffff !important;             /* White text for active tab */
}

* --- Buttons Styling --- */
.stButton>button {
    color: #ffffff !important;             /* White text for buttons */
}


/* Progress bar */
.stProgress > div > div {
    background-color: #4CAF50 !important;
}

/* Correct / incorrect answers */
.score-correct {
    color: #006400 !important;
    font-weight: bold !important;
}

.score-incorrect {
    color: #8b0000 !important;
    font-weight: bold !important;
}
</style>
""", unsafe_allow_html=True)


# --- Session State Initialization ---
for key in ['pdf_file_name', 'pdf_text_content', 'pdf_db_id', 'summary_text', 
            'quiz_data', 'user_answers', 'quiz_submitted']:
    if key not in st.session_state:
        st.session_state[key] = None if key not in ['user_answers', 'quiz_submitted'] else {} if key == 'user_answers' else False

# --- Sidebar ---
with st.sidebar:
    st.title("📚 Study Agent")
    st.header("Upload PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    st.subheader("Instructions")
    st.markdown("""
    1. Upload a PDF file using the "Choose a PDF file" button above.
    2. Once the PDF is uploaded and text is extracted, navigate to the "PDF Summary" tab.
    3. Click "Generate Summary" to get a summary of your PDF content.
    4. After the summary is generated, go to the "Quiz Generator" tab.
    5. Click "Create Quiz" to generate interactive multiple-choice and mixed questions.
    6. Answer the quiz questions and click "Check Answers" to see your score and results.
    All uploaded PDFs, generated summaries, and quizzes are saved to a local database.
    """)

    if uploaded_file:
        if st.session_state.pdf_file_name != uploaded_file.name:
            st.session_state.pdf_file_name = uploaded_file.name
            st.session_state.pdf_text_content = None
            st.session_state.pdf_db_id = None
            st.session_state.summary_text = None
            st.session_state.quiz_data = None
            st.session_state.user_answers = {}
            st.session_state.quiz_submitted = False
            st.success(f"Loaded: {uploaded_file.name}")

        if st.session_state.pdf_text_content is None:
            with st.spinner("Extracting text from PDF..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                text = study_agent.extract_text_from_pdf(tmp_file_path)
                os.unlink(tmp_file_path)
                if text:
                    st.session_state.pdf_text_content = text
                    conn = connect_db()
                    st.session_state.pdf_db_id = insert_pdf_data(conn, uploaded_file.name, text)
                    conn.close()
                    st.success("Text extracted and saved to database!")
                else:
                    st.error("Failed to extract text from PDF.")
                    st.session_state.pdf_file_name = None

# --- Main Content ---
st.title("📚 Study Notes Summarizer & Quiz Generator")
tab_summary, tab_quiz = st.tabs(["📄 PDF Summary", "🧠 Quiz Generator"])

# --- PDF Summary Tab ---
with tab_summary:
    st.header("PDF Summary")
    existing_summary = None
    if st.session_state.pdf_db_id:
        conn = connect_db()
        existing_summary = get_summary(conn, st.session_state.pdf_db_id)
        conn.close()

    if existing_summary:
        st.session_state.summary_text = existing_summary['summary_text']
        st.info("Loaded previous summary from database.")

    if st.session_state.summary_text:
        st.markdown(f'<div class="stCard"><h3>Summary</h3><p>{st.session_state.summary_text}</p></div>', unsafe_allow_html=True)
    else:
        if st.button("Generate Summary", disabled=not st.session_state.pdf_db_id):
            with st.spinner("Generating summary using Gemini..."):
                summary = study_agent.summarize_text(st.session_state.pdf_text_content)
                if summary:
                    st.session_state.summary_text = summary
                    conn = connect_db()
                    insert_summary(conn, st.session_state.pdf_db_id, summary)
                    conn.close()
                    st.markdown(f'<div class="stCard"><h3>Summary</h3><p>{st.session_state.summary_text}</p></div>', unsafe_allow_html=True)
                else:
                    st.error("Failed to generate summary.")
        elif not st.session_state.pdf_db_id:
            st.info("Please upload a PDF file from the sidebar to get started.")

# --- Quiz Generator Tab ---
with tab_quiz:
    st.header("Quiz Generator")
    # Load existing quiz
    existing_quiz = None
    if st.session_state.pdf_db_id:
        conn = connect_db()
        existing_quiz = get_quiz(conn, st.session_state.pdf_db_id)
        conn.close()
        if existing_quiz:
            st.session_state.quiz_data = existing_quiz['quiz_data']
            st.info("Loaded previous quiz from database.")

    if st.session_state.summary_text:  # Only allow quiz if summary exists
        if st.session_state.quiz_data:
            st.subheader("Answer the Quiz Questions")
            # Display MCQs
            total_questions = len(st.session_state.quiz_data.get('mcqs', [])) + \
                              len(st.session_state.quiz_data.get('mixed_questions', []))

            for i, mcq in enumerate(st.session_state.quiz_data.get('mcqs', [])):
                st.markdown(f'<div class="stCard"><h4>Question {i+1}: {mcq["question"]}</h4>', unsafe_allow_html=True)
                options_display = [opt for opt in mcq["options"]]
                user_choice = st.radio(
                    "Select your answer:",
                    options_display,
                    key=f"mcq_{i}",
                    index=None,
                    disabled=st.session_state.quiz_submitted
                )
                if user_choice:
                    st.session_state.user_answers[f"mcq_{i}"] = user_choice
                st.markdown('</div>', unsafe_allow_html=True)

            # Display Mixed Questions
            mcq_count = len(st.session_state.quiz_data.get('mcqs', []))
            for i, mixed_q in enumerate(st.session_state.quiz_data.get('mixed_questions', [])):
                q_num = mcq_count + i + 1
                st.markdown(f'<div class="stCard"><h4>Question {q_num}: {mixed_q["question"]}</h4>', unsafe_allow_html=True)
                if mixed_q["type"] == "true_false":
                    user_tf_choice = st.radio(
                        "Select True or False:",
                        ["True", "False"],
                        key=f"mixed_{i}",
                        index=None,
                        disabled=st.session_state.quiz_submitted
                    )
                    if user_tf_choice:
                        st.session_state.user_answers[f"mixed_{i}"] = user_tf_choice
                elif mixed_q["type"] == "fill_in_the_blank":
                    user_fill_answer = st.text_input(
                        "Fill in the blank:",
                        key=f"mixed_{i}",
                        disabled=st.session_state.quiz_submitted
                    )
                    if user_fill_answer:
                        st.session_state.user_answers[f"mixed_{i}"] = user_fill_answer
                st.markdown('</div>', unsafe_allow_html=True)

            if st.button("Check Answers", disabled=st.session_state.quiz_submitted):
                st.session_state.quiz_submitted = True
                score = 0
                results = []

                # Evaluate MCQs
                for i, mcq in enumerate(st.session_state.quiz_data.get('mcqs', [])):
                    user_ans = st.session_state.user_answers.get(f"mcq_{i}")
                    correct_ans_letter = mcq["correct_answer"]
                    correct_option_full = next((opt for opt in mcq["options"] if opt.startswith(correct_ans_letter + ".")), None)
                    is_correct = user_ans and correct_option_full and user_ans.strip() == correct_option_full.strip()
                    if is_correct: score += 1
                    results.append({"question": mcq["question"], "user_answer": user_ans, "correct_answer": correct_option_full, "is_correct": is_correct})

                # Evaluate Mixed Questions
                for i, mixed_q in enumerate(st.session_state.quiz_data.get('mixed_questions', [])):
                    user_ans = st.session_state.user_answers.get(f"mixed_{i}")
                    is_correct = False
                    if mixed_q["type"] == "true_false" and user_ans and user_ans.lower() == mixed_q["correct_answer"].lower():
                        is_correct = True
                        score += 1
                    elif mixed_q["type"] == "fill_in_the_blank" and user_ans and user_ans.lower() == mixed_q["correct_answer"].lower():
                        is_correct = True
                        score += 1
                    results.append({"question": mixed_q["question"], "user_answer": user_ans, "correct_answer": mixed_q["correct_answer"], "is_correct": is_correct})

                st.subheader("Quiz Results")
                if results:
                    st.progress(score / len(results), text=f"Your Score: {score}/{len(results)}")
                for res in results:
                    color_class = "score-correct" if res["is_correct"] else "score-incorrect"
                    st.markdown(f'<div class="stCard"><p><strong>Q:</strong> {res["question"]}</p>'
                                f'<p>Your Answer: <span class="{color_class}">{res["user_answer"] if res["user_answer"] else "Not Answered"}</span></p>'
                                f'<p>Correct Answer: <span class="score-correct">{res["correct_answer"]}</span></p></div>', unsafe_allow_html=True)

                # Save quiz attempt
                conn = connect_db()
                quiz_record = get_quiz(conn, st.session_state.pdf_db_id)
                if quiz_record:
                    insert_quiz_attempt(conn, quiz_record['id'], st.session_state.user_answers, score)
                    st.success("Quiz attempt saved to database!")
                conn.close()

        else:  # No quiz yet, show "Create Quiz" button
            if st.button("Create Quiz"):
                with st.spinner("Generating quiz using Gemini... This may take a moment."):
                    quiz = study_agent.generate_quiz(st.session_state.pdf_text_content)
                    if quiz:
                        st.session_state.quiz_data = quiz
                        st.session_state.user_answers = {}
                        st.session_state.quiz_submitted = False
                        conn = connect_db()
                        insert_quiz(conn, st.session_state.pdf_db_id, quiz)
                        conn.close()
                        st.rerun()
                    else:
                        st.error("Failed to generate quiz. Please try again.")
    else:
        st.info("Generate a summary in the 'PDF Summary' tab first to enable quiz generation.")


