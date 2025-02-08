import os
from PyPDF2 import PdfReader
import streamlit as st
import google.generativeai as genai
import time


def save_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        with open("context.txt", "w", encoding='utf-8') as file:
            for page in pdf_reader.pages:
                file.write(page.extract_text())


def main():
    st.set_page_config(
        page_title="Gemini PDF Chatbot",
        page_icon="🤖"
    )

    model_option = st.selectbox(
        "Select a model to query:",
        ("Gemini 2.0 Flash Thinking",
         "Gemini 2.0 Flash",
         "Gemini 2.0 Pro",
         )
    )

    print(f"当前选择的模型：{model_option}")
    model_dict = {"Gemini 2.0 Flash Thinking": "models/gemini-2.0-flash-thinking-exp",
                  "Gemini 2.0 Flash": "models/gemini-2.0-flash",
                  "Gemini 2.0 Pro": "models/gemini-2.0-pro-exp"}

    markdown_name = "test.md"

    # Initialize markdown cache filename
    if 'markdown_name' not in st.session_state:
        st.session_state.markdown_name = markdown_name
    else:
        markdown_name = st.session_state.markdown_name

    with st.sidebar:
        Gemini_API_KEY = st.text_input("Please input Gemini API", type="password")

        # File uploader for PDFs
        pdf_docs = st.file_uploader(
            "Upload your PDF Files", accept_multiple_files=True)

        # Convert uploaded PDFs to text files
        if st.button("Submit & Process"):
            with st.spinner("Processing..."):
                save_pdf_text(pdf_docs)
                st.success("Done")
                markdown_name = pdf_docs[0].name.replace("pdf", "md")
                st.session_state.markdown_name = markdown_name
                print("markdown name from file：", st.session_state.markdown_name)

        # Clear chat history, including messages and cached chat objects
        if st.button("Clear chat history"):
            with st.spinner("Processing..."):
                del st.session_state.chat_session
                st.session_state.messages = [
                    {"role": "assistant", "content": "Ask me a question"}
                ]
                st.success("Done")

    # Configure language model
    genai.configure(api_key=Gemini_API_KEY)
    model = genai.GenerativeModel(model_name=model_dict[model_option],
                                  system_instruction="You are a senior professional securities analyst. Please respond in Chinese.")

    # Initialize chat object
    chat = model.start_chat(history=[])

    # Initialize chat session
    if 'chat_session' not in st.session_state:
        st.session_state.chat_session = chat
    else:
        chat = st.session_state.chat_session

    # Initialize messages
    if "messages" not in st.session_state.keys():
        st.session_state.messages = [
            {"role": "assistant", "content": "Ask me a question"}
        ]

    # Display all chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Read user input and display on the web page
    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.spinner("Thinking..."):
            # If it's the first round, load context
            context = ""
            with open("context.txt", 'r', encoding='utf-8') as f:
                text_docs = f.read()
            if len(text_docs) != 0:
                context = text_docs
                with open("context.txt", 'w', encoding='utf-8') as f:
                    f.truncate(0)

            while True:
                try:
                    response = chat.send_message(context + prompt)
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    time.sleep(10)

            st.markdown(response.text)

            with open(st.session_state.markdown_name, 'a', encoding='utf-8') as f:
                f.write(response.text + '\n')

            print(model.count_tokens(chat.history))

            # Cache chat session for next round
            st.session_state.chat_session = chat

            # Cache response for next round
            if response is not None:
                message = {"role": "assistant", "content": response.text}
                st.session_state.messages.append(message)

    with st.sidebar:
        try:
            with open(st.session_state.markdown_name, "rb") as file:
                btn = st.download_button(
                    label="Download file",
                    data=file,
                    file_name=st.session_state.markdown_name,
                )
        except FileNotFoundError:
             print(f"file {st.session_state.markdown_name} not exist.")

if __name__ == "__main__":
    main()
