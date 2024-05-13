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
    # 设置网页信息
    st.set_page_config(
        page_title="Gemini PDF Chatbot",
        page_icon="🤖"
    )
    # 配置css
    with open("streamlit.css") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

    # 设置网页标题
    st.title("Chat with PDF files using Gemini")
    st.write("Welcome to the chat!")

    markdown_path = "README.md"

    # 初始化缓存markdown 文件名
    if 'markdown_path' not in st.session_state:
        st.session_state.markdown_name = markdown_path
    else:
        markdown_path = st.session_state.markdown_path

    with st.sidebar:
        Gemini_API_KEY = st.text_input("Please input Gemini API", type="password")
        # 上传文件框
        pdf_docs = st.file_uploader(
            "Upload your PDF Files and Click on the Submit & Process Button", accept_multiple_files=True)

        # 上传的PDF转换成txt文件
        if st.button("Submit & Process"):
            with st.spinner("Processing..."):
                save_pdf_text(pdf_docs)
                st.success("Done")
                markdown_name = pdf_docs[0].name.replace("pdf", "md")
                st.session_state.markdown_path = markdown_name
                print(st.session_state.markdown_path)

        # 清空对话历史，包括消息记录，缓存的chat对象
        if st.button("clear chat history"):
            with st.spinner("Processing..."):
                del st.session_state.chat_session
                st.session_state.messages = [
                    {"role": "assistant", "content": "ask me a question"}]
                st.success("Done")

        with open(st.session_state.markdown_name, "rb") as file:
            btn = st.download_button(
                label="Download file",
                data=file,
                file_name=st.session_state.markdown_name,

            )

    # 配置语言模型
    genai.configure(api_key=Gemini_API_KEY)
    model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest",
                                  system_instruction="你是一名资深专业证券分析师，请用中文回答")

    # 初始化chat对象
    chat = model.start_chat(history=[])

    # 初始化chat
    if 'chat_session' not in st.session_state:
        st.session_state.chat_session = chat
    else:
        chat = st.session_state.chat_session

    # 初始化messages
    if "messages" not in st.session_state.keys():
        st.session_state.messages = [
            {"role": "assistant", "content": "ask me a question"}]

    # 显示所有对话信息
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # 读取用户输入，并在网页上显示
    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # if st.session_state.messages[-1]["role"] != "assistant":
        #     with st.chat_message("assistant"):
        with st.spinner("Thinking..."):

            # 如果第一轮，则加载上下文
            context = ""
            with open("context.txt", 'r', encoding='utf-8') as f:
                text_docs = f.read()
            if len(text_docs) != 0:
                context = text_docs
                with open("context.txt", 'w', encoding='utf-8') as f:
                    f.truncate(0)
            print(context)
            print(prompt)

            while True:
                try:
                    # 获取大语言模型回复
                    response = chat.send_message(context + prompt)
                    break  # 如果成功，则跳出循环
                except Exception as e:
                    # 处理异常并继续重试
                    print(f"错误：{e}")
                    time.sleep(10)  # 等待 10 秒

            # 网页显示markdown
            st.markdown(response.text)
            print(markdown_path)

            # 保存大语言模型回复到磁盘
            with open(markdown_path, 'a', encoding='utf-8') as f:
                f.write(response.text + '\n')

            # 终端输出回复
            print(response.text)
            print(model.count_tokens(chat.history))
            # 缓存chat_session，以便下轮使用
            st.session_state.chat_session = chat

            # 缓存大语言回复，以便下轮使用
            if response is not None:
                message = {"role": "assistant", "content": response.text}
                st.session_state.messages.append(message)


if __name__ == "__main__":
    main()
