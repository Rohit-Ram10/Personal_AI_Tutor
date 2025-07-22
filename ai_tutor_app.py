import os
import streamlit as st
import google.generativeai as genai
import speech_recognition as sr  
import pyttsx3  
from gtts import gTTS 
import pandas as pd
from datetime import datetime

if 'quiz_history' not in st.session_state:
    st.session_state['quiz_history'] = []


def calculate_score(user_answers, correct_answers):
    correct_count = sum([ua[0] == ca for ua, ca in zip(user_answers, correct_answers)])
    score = (correct_count/len(user_answers))*100 if user_answers else 0
    return score

def process_quiz_submission(quiz_topic, quiz_data, user_answers):
    correct_answers = quiz_data["correct_answers"]
    score = calculate_score(user_answers, correct_answers)
    quiz_record = {
        "student_name": st.session_state.get('student_name', 'Anonymous'),
        "grade_year": st.session_state.get('grade_year', 'Not specified'),
        "quiz_topic": quiz_topic,
        "questions": quiz_data["questions"],
        "user_answers": user_answers,
        "correct_answers": correct_answers,
        "score": score,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    st.session_state['quiz_history'].append(quiz_record)

def display_quiz_details(quiz_record):
    st.markdown(f"**Quiz Topic:** {quiz_record['quiz_topic']}")
    st.markdown(f"**Score:** {quiz_record['score']:.1f}%")


    st.markdown(f"**Date:** {quiz_record['timestamp']}")
    
    st.markdown("---")
    st.markdown("### Question Details")
    
    for i, (question, user_answer, correct_answer) in enumerate(zip(
        quiz_record['questions'],
        quiz_record['user_answers'],
        quiz_record['correct_answers']
    )):
        st.markdown(f"**Question {i+1}:** {question['question']}")
        st.markdown(f"- Your Answer: {user_answer}")
        st.markdown(f"- Correct Answer: {correct_answer}")
        st.markdown(f"- Result: {'✅ Correct' if user_answer[0] == correct_answer else '❌ Incorrect'}")
        st.markdown("---")

def generate_pdf_report(quiz_history):
    from fpdf import FPDF
    import tempfile
    import os
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Add student information
    if quiz_history:
        pdf.cell(200, 10, txt=f"Student Name: {quiz_history[0]['student_name']}", ln=1)
        pdf.cell(200, 10, txt=f"Grade/Year: {quiz_history[0]['grade_year']}", ln=1)
        pdf.ln(10)
    
    # Add quiz results
    for quiz in quiz_history:
        pdf.set_font("Arial", 'B', size=14)
        pdf.cell(200, 10, txt=f"Quiz: {quiz['quiz_topic']}", ln=1)
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Score: {quiz['score']:.1f}%", ln=1)
        pdf.cell(200, 10, txt=f"Date: {quiz['timestamp']}", ln=1)
        pdf.ln(5)
        
        # Add question details
        for i, (question, user_answer, correct_answer) in enumerate(zip(
            quiz['questions'],
            quiz['user_answers'],
            quiz['correct_answers']
        )):
            pdf.cell(200, 10, txt=f"Question {i+1}: {question['question']}", ln=1)
            pdf.cell(200, 10, txt=f"- Your Answer: {user_answer}", ln=1)
            pdf.cell(200, 10, txt=f"- Correct Answer: {correct_answer}", ln=1)
            pdf.cell(200, 10, txt=f"- Result: {'✅ Correct' if user_answer[0] == correct_answer else '❌ Incorrect'}", ln=1)
            pdf.ln(3)
        pdf.ln(10)
    
    # Save to temp file
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, "quiz_report.pdf")
    pdf.output(file_path)
    return file_path

def display_progress_dashboard():
    import os
    if not st.session_state['quiz_history']:
        st.write("No quiz history available.")
        return

    # Display student information
    st.subheader("Student Information")
    col1, col2 = st.columns(2)
    col1.metric("Name", st.session_state.get('student_name', 'Anonymous'))
    col2.metric("Grade/Year", st.session_state.get('grade_year', 'Not specified'))

    # Performance overview
    st.subheader("Performance Overview")
    df = pd.DataFrame(st.session_state['quiz_history'])
    df_display = df[["quiz_topic","score","timestamp"]]
    st.dataframe(df_display)

    # Show chart
    chart_data = df.groupby("quiz_topic").agg({"score":"mean"}).reset_index()
    st.bar_chart(data=chart_data,x="quiz_topic", y="score", height=400)

    # Detailed results with expandable sections
    st.subheader("Detailed Quiz Results")
    for i, quiz_record in enumerate(st.session_state['quiz_history']):
        with st.expander(f"Quiz {i+1}: {quiz_record['quiz_topic']} ({quiz_record['score']:.1f}%)"):
            display_quiz_details(quiz_record)

    # Export options
    st.subheader("Export Options")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Download PDF Report"):
            report_path = generate_pdf_report(st.session_state['quiz_history'])
            with open(report_path, "rb") as file:
                st.download_button(
                    label="Download PDF",
                    data=file,
                    file_name="quiz_report.pdf",
                    mime="application/pdf"
                )
    
    with col2:
        if st.button("Generate Shareable Link"):
            # Generate unique ID for this report
            import uuid
            import json
            report_id = str(uuid.uuid4())
            
            # Create temporary shareable data
            share_data = {
                "student_name": st.session_state.get('student_name', 'Anonymous'),
                "grade_year": st.session_state.get('grade_year', 'Not specified'),
                "quiz_history": st.session_state['quiz_history']
            }
            
            # Save to memlog folder
            os.makedirs("memlog", exist_ok=True)
            report_path = os.path.join("memlog", f"{report_id}.json")
            with open(report_path, "w") as f:
                json.dump(share_data, f)
                
            # Generate shareable link
            base_url = "http://localhost:8501"  # Streamlit default URL
            share_url = f"{base_url}/?report_id={report_id}"
            
            st.success("Shareable link generated!")
            st.markdown(f"**Share this link:** [{share_url}]({share_url})")
            st.info("Note: The link will only work while the app is running.")


def main():
    st.set_page_config(page_title="AI Tutor 👨‍🎓🤖", page_icon="🤖")
    
    # Header with logo
    col1, col2 = st.columns([1, 4])
    with col1:
        image_url = "assets/Logo.png"
        st.image(image_url, caption="Learn-Grow-Succeed", use_container_width=True)
    with col2:
        st.title("Personal AI Tutor 👨‍🎓🤖")
        st.caption("Discover interactive learning with our AI-powered tutor app. A smart solution to empower students and enhance their educational experience.")

    # Student information section
    if 'student_name' not in st.session_state:
        st.subheader("Student Information")
        with st.form("student_info"):
            name = st.text_input("Your Name", placeholder="Enter your name")
            grade = st.selectbox(
                "Grade/Year",
                options=["Not specified", "Grade 1", "Grade 2", "Grade 3", 
                        "Grade 4", "Grade 5", "Grade 6", "Grade 7", 
                        "Grade 8", "Grade 9", "Grade 10", "Grade 11", 
                        "Grade 12", "College"]
            )
            
            if st.form_submit_button("Save Information"):
                if name.strip():
                    st.session_state['student_name'] = name
                    st.session_state['grade_year'] = grade
                    st.success("Information saved!")
                else:
                    st.error("Please enter your name")
        
        if 'student_name' not in st.session_state:
            st.warning("Please provide your information before continuing")
            return


    st.markdown("""
    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
        <span style="color: orange; font-size: 1.2em;">⚠️</span>
        <span>Get your API key from <a href="https://aistudio.google.com/" target="_blank">Google AI Studio</a></span>
    </div>
    """, unsafe_allow_html=True)
    
    google_api_key = st.text_input("Google API Key", type="password")
    if not google_api_key:
        st.warning("Please enter your Google API key")
        return

    try:
        genai.configure(api_key=google_api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"Failed to initialize Gemini: {e}")
        return

    # Interactive Learning
    # Voice Input for AI Chat
    

    # Normal text input
    query = st.text_input("Ask a question or specify a topic to learn", placeholder="Type your question or topic here...", key="typed_query")

    if query:
        with st.spinner("Generating response..."):
            try:
                response = model.generate_content(f"Explain {query} clearly with examples")
                st.markdown("### AI Tutor's Response")
                st.write(response.text)


            except Exception as e:
                st.error(f"Error: {e}")

    # Quiz Generator
    quiz_topic = st.text_input("Enter a topic to generate a quiz", placeholder="Type a topic for your quiz...")
    if quiz_topic:
        with st.spinner("Generating quiz..."):
            try:
                # Use a more structured prompt format
                prompt = f"""
                Create a 5-question multiple-choice quiz about {quiz_topic}.
                Format each question EXACTLY like this:
                
                Question 1: [question text]
                A) [option A]
                B) [option B]
                C) [option C]
                D) [option D]
                Correct Answer: [A/B/C/D]
                
                Repeat this format for all 5 questions.
                """
                
                quiz = model.generate_content(prompt)
                quiz_text = quiz.text
                
                # Parse quiz into structured format
                questions = []
                correct_answers = []
                
                # Split into individual questions
                question_blocks = quiz_text.split("Question ")
                for block in question_blocks:
                    if not block.strip():
                        continue
                    
                    lines = [line.strip() for line in block.split("\n") if line.strip()]
                    
                    # We need at least 6 lines: question + 4 options + answer
                    if len(lines) < 6:
                        continue
                        
                    try:
                        # First line should be the question number and text
                        question_text = lines[0].split(":", 1)[1].strip()
                        
                        # Next 4 lines should be options
                        options = []
                        for i in range(1, 5):
                            if lines[i].startswith(('A)', 'B)', 'C)', 'D)')):
                                options.append(lines[i])
                            else:
                                break
                                
                        # Last line should be the correct answer
                        correct_answer = ""
                        if lines[-1].lower().startswith("correct answer:"):
                            correct_answer = lines[-1].split(":")[-1].strip().upper()
                            
                        # Validate we have all required components
                        if (question_text and 
                            len(options) == 4 and 
                            all(opt.startswith(('A)', 'B)', 'C)', 'D)')) for opt in options) and
                            correct_answer in ['A', 'B', 'C', 'D']):
                            
                            questions.append({
                                "question": question_text,
                                "options": options
                            })
                            correct_answers.append(correct_answer)
                            
                    except Exception as e:
                        st.warning(f"Skipping malformed question: {e}")
                        continue
            
                if not questions:
                    st.error("Failed to parse any valid quiz questions. Please try again with a different topic.")
                    return
                
                # Store quiz data in session state if not already present
                if 'current_quiz' not in st.session_state:
                    st.session_state['current_quiz'] = {
                        "data": {
                            "questions": questions,
                            "correct_answers": correct_answers
                        },
                        "user_answers": [None] * len(questions)
                    }
                
                quiz_data = st.session_state['current_quiz']['data']
                user_answers = st.session_state['current_quiz']['user_answers']
                
                st.markdown("### Quiz")
                for i, question in enumerate(quiz_data['questions']):
                    st.markdown(f"**{i+1}. {question['question']}**")
                    # Display the full answer choices with text
                    options_with_text = [
                        f"{question['options'][0]}",
                        f"{question['options'][1]}", 
                        f"{question['options'][2]}",
                        f"{question['options'][3]}"
                    ]
                    
                    # Use a unique key combining quiz topic and question index
                    unique_key = f"{quiz_topic}_q_{i}"
                    
                    # Get current answer or None if not answered yet
                    current_answer = user_answers[i]
                    
                    # Create radio button with current selection
                    user_answer = st.radio(
                    f"Select your answer for question {i+1}",
                    options=options_with_text,
                    index=options_with_text.index(current_answer) if current_answer else 0,
                    key=unique_key
                )

                

                    
                    # Update answer in session state
                    if user_answer:
                        user_answers[i] = user_answer  # Store the full selected answer text
                        st.session_state['current_quiz']['user_answers'] = user_answers
                
                if st.button("Submit Quiz"):
                    process_quiz_submission(quiz_topic, quiz_data, user_answers)
                    st.success("Quiz submitted successfully!")
                    st.balloons()
                
            except Exception as e:
                st.error(f"Error: {e}")

        # Display progress dashboard
        display_progress_dashboard()

if __name__ == "__main__":
    main()
