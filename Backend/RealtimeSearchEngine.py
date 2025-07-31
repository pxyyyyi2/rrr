from googlesearch import search
from groq import Groq
from json import load, dump
from datetime import datetime
from dotenv import dotenv_values

# Load environment variables from the .env file.
env_vars = dotenv_values(".env")

# Retrieve environment variables for the chatbot configuration.
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")

# Initialize the Groq client with the provided API key.
client = Groq(api_key=GroqAPIKey)

# Define the system instructions for the chatbot.
System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which has real-time up-to-date data.
*** Provide Answers In a Professional Way, make sure to add full stops, commas, question marks, and use proper grammar. ***
*** Just answer the question from the provided data in a professional way. ***"""

# Try to load the chat log from a JSON file, or create an empty one if it doesn't exist.
try:
    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)
except:
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)

# Function to clean up the answer by removing empty lines.
def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

# Function to perform a Google search and format the results (TRUNCATED).
def GoogleSearch(query):
    results = list(search(query, advanced=True, num_results=3))  # Reduced from 5 to 3
    Answer = f"Search results for {query}:\n"

    for i, result in enumerate(results, 1):
        # Truncate title and description to prevent token overflow
        title = result.title[:100] + "..." if len(result.title) > 100 else result.title
        description = result.description[:200] + "..." if len(result.description) > 200 else result.description
        Answer += f"{i}. {title}\n{description}\n\n"

    return Answer

# Function to get real-time information like the current date and time.
def Information():
    current_date_time = datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")

    data = f"Current Info: {day}, {month} {date}, {year} at {hour}:{minute}"
    return data

# Function to limit chat history to prevent token overflow
def limit_chat_history(messages, max_messages=4):
    """Keep only the last few messages to stay within token limits"""
    if len(messages) > max_messages:
        return messages[-max_messages:]
    return messages

# Function to handle real-time search and response generation.
def RealtimeSearchEngine(prompt):
    global messages

    # Load the chat log from the JSON file.
    try:
        with open(r"Data\ChatLog.json", "r") as f:
            messages = load(f)
    except:
        messages = []

    # Limit chat history to prevent token overflow
    limited_messages = limit_chat_history(messages, max_messages=3)
    
    # Add current user prompt
    current_conversation = limited_messages + [{"role": "user", "content": prompt}]

    # Get search results and current time info
    search_results = GoogleSearch(prompt)
    time_info = Information()

    # Create a concise system message with search results
    system_with_search = f"""{System}

{time_info}

{search_results}

Answer the user's question based on the search results above."""

    # Build the final message list (keeping it minimal)
    final_messages = [
        {"role": "system", "content": system_with_search}
    ] + current_conversation

    try:
        # Generate a response using the Groq client with higher capacity model
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Current production model with 128K context
            messages=final_messages,
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stream=True,
            stop=None
        )

        # Concatenate response chunks from the streaming output.
        Answer = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content

        # Clean up the response.
        Answer = Answer.strip().replace("</s>", "")
        
        # Add to messages and save
        messages.append({"role": "user", "content": prompt})
        messages.append({"role": "assistant", "content": Answer})

        # Save the updated chat log back to the JSON file.
        with open(r"Data\ChatLog.json", "w") as f:
            dump(messages, f, indent=4)

        return AnswerModifier(Answer=Answer)

    except Exception as e:
        print(f"Error: {e}")
        # Fallback to smaller model with even more limited context
        try:
            fallback_messages = [
                {"role": "system", "content": f"{System}\n{search_results}"},
                {"role": "user", "content": prompt}
            ]
            
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=fallback_messages,
                temperature=0.7,
                max_tokens=512,
                top_p=1,
                stream=True,
                stop=None
            )

            Answer = ""
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    Answer += chunk.choices[0].delta.content

            Answer = Answer.strip().replace("</s>", "")
            return AnswerModifier(Answer=Answer)
            
        except Exception as fallback_error:
            return f"Sorry, I encountered an error: {fallback_error}"

# Main entry point of the program for interactive querying.
if __name__ == "__main__":
    while True:
        prompt = input("Enter your query: ")
        if prompt.lower() in ['quit', 'exit', 'bye']:
            break
        print(RealtimeSearchEngine(prompt))