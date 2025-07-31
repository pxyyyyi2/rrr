from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values
import os

# Load configuration from .env
env = dotenv_values(".env")
user_name = env.get("Username")
bot_name = env.get("Assistantname")
groq_api_key = env.get("GroqAPIKey")

# Initialize Groq client
groq_client = Groq(api_key=groq_api_key)

# Create folder to store chat logs
os.makedirs("Data", exist_ok=True)

# Load chat history if available
try:
    with open("Data/ChatLog.json", "r") as file:
        chat_history = load(file)
except FileNotFoundError:
    chat_history = []

# System message template
system_prompt = f"""Hello, I am {user_name}, You are a very accurate and advanced AI chatbot named {bot_name} which has real-time up-to-date information from the internet.
*** Provide Answers In a Professional Way, make sure to add full stops, commas, question marks, and use proper grammar.***
*** Just answer the question from the provided data in a professional way. ***
"""

# Format system message for model input
system_message = [{"role": "system", "content": system_prompt}]

# Provide current date and time
def get_real_time_info():
    now = datetime.datetime.now()
    return (
        f"Please use this real-time information if needed.\n"
        f"Day: {now.strftime('%A')}\n"
        f"Date: {now.strftime('%d')}\n"
        f"Month: {now.strftime('%B')}\n"
        f"Year: {now.strftime('%Y')}.\n"
        f"Time: {now.strftime('%H')} hours:{now.strftime('%M')} minutes:{now.strftime('%S')} seconds.\n"
    )

# Clean up the assistant's response
def format_response(response):
    lines = response.split('\n')
    return '\n'.join([line for line in lines if line.strip()])

# Core chatbot function
def handle_chat(user_input):
    global chat_history
    try:
        chat_history.append({"role": "user", "content": user_input})

        response_stream = groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=system_message + [{"role": "system", "content": get_real_time_info()}] + chat_history,
            max_tokens=1024,
            temperature=0.7,
            top_p=1,
            stream=True
        )

        full_response = ""
        for chunk in response_stream:
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content

        full_response = full_response.replace("</s>", "")
        chat_history.append({"role": "assistant", "content": full_response})

        with open("Data/ChatLog.json", "w") as file:
            dump(chat_history, file, indent=4)

        return format_response(full_response)

    except Exception as error:
        print(f"Error: {error}")
        chat_history = []
        with open("Data/ChatLog.json", "w") as file:
            dump(chat_history, file, indent=4)
        return handle_chat(user_input)

# Command-line interface
if __name__ == "__main__":
    while True:
        user_input = input("Tell me sir, what can I do for you? ")
        print(handle_chat(user_input))
