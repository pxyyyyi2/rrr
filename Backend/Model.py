import cohere
from rich import print
from dotenv import dotenv_values

# Load environment variables
environment = dotenv_values(".env")
api_key = environment.get("CohereAPIkey")

# Initialize Cohere client
client = cohere.Client(api_key=api_key)

# List of supported command prefixes - REMOVED RESTRICTIVE FILTERING
prefixes = [
    "exit", "general", "open", "close", "play",
    "generate image", "system", "content", "google search",
    "youtube search", "reminder", "realtime"
]

history = []  # Store user and assistant messages

instruction = """
You are a smart AI that classifies user queries into categories. Do not answer the query. Just return its type.

Respond like this:
- 'general (query)' → For questions a normal AI can answer, conversations, explanations, help with topics. E.g., 'What is Python?', 'How to study better?', 'tell me about tickets', 'explain machine learning', 'help me with coding'
- 'realtime (query)' → For questions needing latest/current info or about current events, famous people, news. E.g., 'Who is current Indian PM?', 'Latest cricket news?', 'today's weather'
- 'open (app/website)' → For commands to open apps or websites. E.g., 'open YouTube', 'open Chrome and Facebook'
- 'close (app/website)' → For commands to close apps. E.g., 'close WhatsApp', 'close Notepad'
- 'play (song)' → To play music. E.g., 'play Mast Magan', 'play arijit singh songs'
- 'generate image (prompt)' → To generate images from prompts. E.g., 'generate image of doraemon'
- 'reminder (date time message)' → To set reminders. E.g., 'reminder 9pm 25th June meeting'
- 'system (action)' → For system commands. E.g., 'system mute', 'system volume up'
- 'content (topic)' → For content generation like applications, emails, code. E.g., 'content write email for leave'
- 'google search (topic)' → For Google searches. E.g., 'google search Elon Musk'
- 'youtube search (topic)' → For YouTube searches. E.g., 'youtube search Python tutorial'

IMPORTANT RULES:
- If the query is about tickets, availability, bookings, events, shows → classify as 'general (query)'
- If the query is a question, explanation request, help request → classify as 'general (query)' 
- If the query needs current/live information → classify as 'realtime (query)'
- If you're unsure, ALWAYS use 'general (query)' as default
- NEVER leave a query unclassified

If multiple actions are requested, list all. E.g., 'open Chrome, close Notepad, reminder 8pm meeting'.

If someone says goodbye like 'bye', respond with: 'exit'

For ANY query that doesn't fit other categories, respond with: 'general (query)'
"""

# Example conversation history - ADDED MORE DIVERSE EXAMPLES
samples = [
    {"role": "User", "message": "how are you?"},
    {"role": "Chatbot", "message": "general how are you?"},
    {"role": "User", "message": "do you like pizza?"},
    {"role": "Chatbot", "message": "general do you like pizza?"},
    {"role": "User", "message": "open chrome and tell me about mahatma gandhi."},
    {"role": "Chatbot", "message": "open chrome, general tell me about mahatma gandhi."},
    {"role": "User", "message": "tell me the available tickets"},
    {"role": "Chatbot", "message": "general tell me the available tickets"},
    {"role": "User", "message": "what tickets are available"},
    {"role": "Chatbot", "message": "general what tickets are available"},
    {"role": "User", "message": "explain machine learning"},
    {"role": "Chatbot", "message": "general explain machine learning"},
    {"role": "User", "message": "help me with python coding"},
    {"role": "Chatbot", "message": "general help me with python coding"},
    {"role": "User", "message": "what's the current weather"},
    {"role": "Chatbot", "message": "realtime what's the current weather"},
    {"role": "User", "message": "latest news about AI"},
    {"role": "Chatbot", "message": "realtime latest news about AI"},
    {"role": "User", "message": "chat with me"},
    {"role": "Chatbot", "message": "general chat with me"}
]

# Function to classify the input query
def classify_input(query: str = "test"):
    try:
        if not query or not query.strip():
            return ["general hello"]
            
        history.append({"role": "user", "content": query})

        response = client.chat_stream(
            model='command-r-plus',
            message=query,
            temperature=0.3,  # Lower temperature for more consistent classification
            chat_history=samples,
            prompt_truncation='OFF',
            connectors=[],
            preamble=instruction,
        )

        complete_reply = ""

        for msg in response:
            if msg.event_type == "text-generation":
                complete_reply += msg.text

        complete_reply = complete_reply.replace("\n", "").strip()
        
        # Handle empty responses
        if not complete_reply:
            print(f"DEBUG - Empty response from Cohere, defaulting to general")
            return [f"general {query}"]
        
        actions = [entry.strip() for entry in complete_reply.split(",")]
        
        # Debug logging
        print(f"DEBUG - Query: '{query}'")
        print(f"DEBUG - Complete reply: '{complete_reply}'")
        print(f"DEBUG - Actions: {actions}")

        # REMOVED RESTRICTIVE FILTERING - Accept all valid classifications
        valid_tasks = []
        for action in actions:
            action = action.strip()
            if action and not action == "(query)":
                # Check if it starts with a known prefix OR contains 'general'
                if (any(action.startswith(prefix) for prefix in prefixes) or 
                    'general' in action or 'realtime' in action):
                    valid_tasks.append(action)
        
        print(f"DEBUG - Valid tasks: {valid_tasks}")

        # Fallback logic - MUCH MORE COMPREHENSIVE
        if not valid_tasks:
            print(f"DEBUG - No valid tasks, applying fallback logic")
            
            query_lower = query.lower()
            
            # Check for specific patterns
            if any(word in query_lower for word in ['current', 'latest', 'today', 'now', 'news', 'weather']):
                return [f"realtime {query}"]
            elif any(word in query_lower for word in ['open', 'launch', 'start']):
                return [f"open {query}"]
            elif any(word in query_lower for word in ['close', 'shut', 'exit']):
                return [f"close {query}"]
            elif any(word in query_lower for word in ['play', 'music', 'song']):
                return [f"play {query}"]
            elif 'generate image' in query_lower or 'create image' in query_lower:
                return [f"generate image {query}"]
            elif 'remind' in query_lower or 'reminder' in query_lower:
                return [f"reminder {query}"]
            elif 'search' in query_lower and 'google' in query_lower:
                return [f"google search {query}"]
            elif 'search' in query_lower and 'youtube' in query_lower:
                return [f"youtube search {query}"]
            else:
                # DEFAULT TO GENERAL FOR EVERYTHING ELSE
                return [f"general {query}"]
        
        return valid_tasks
        
    except Exception as e:
        print(f"ERROR in classify_input: {e}")
        # Robust fallback
        return [f"general {query}"]

# Interactive execution
if __name__ == "__main__":
    print("AI Query Classifier - Type 'quit' to exit")
    print("=" * 50)
    
    while True:
        try:
            user_input = input(">>> ").strip()
            if user_input.lower() in ['quit', 'exit', '']:
                break
                
            result = classify_input(user_input)
            print(f"🤖 Classification: {result}")
            print("-" * 30)
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")