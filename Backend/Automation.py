# Import required libraries
from AppOpener import close, open as appopen # Import open and close apps.
from webbrowser import open as webopen # Webbrowser functionality.
from pywhatkit import search, playonyt # Google search and YouTube playback.
from dotenv import dotenv_values # Import environment variables.
from bs4 import BeautifulSoup # For parsing HTML content.
from rich import print # Import Rich for styled console output.
from groq import Groq # Import Groq for API call
import requests
import subprocess # Import subprocess for running terminal commands.
import webbrowser # Import webbrowser for web functionality.
import keyboard # Import keyboard for keyboard-related actions. 
import asyncio # Import asyncio for asynchronous operations.
import os # Import os for operating system functionality.
from datetime import datetime # Import datetime for date formatting
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from the .env file.
env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey") # Retrieve the Groq API key.

# Initialize the Groq Client with the API key.
Client = Groq(api_key=GroqAPIKey)

# List to store chatbot messages.
messages = []

# System message to provide context to the chatbot.
SystemChatBot = [{ 
    "role": "system", 
    "content": f"Hello, I am {os.environ.get('USERNAME', 'User')}. You're a content writer. You have to write content like letters, codes, applications, essays, notes, songs, poems etc." 
}]

def GoogleSearch(Topic):
    """Perform a Google search for the given topic"""
    try:
        logger.info(f"Performing Google search for: {Topic}")
        search(Topic)
        return True
    except Exception as e:
        logger.error(f"Error in Google search: {e}")
        # Fallback to opening Google search in browser
        webopen(f"https://www.google.com/search?q={Topic.replace(' ', '+')}")
        return True

def generate_sick_leave_letter():
    """Generate a basic sick leave letter template"""
    try:
        logger.info("Generating sick leave letter")
        today = datetime.now().strftime("%B %d, %Y")
        
        letter = f"""Date: {today}

To,
The Manager/HR Department
[Company Name]
[Company Address]

Subject: Application for Sick Leave

Dear Sir/Madam,

I am writing to inform you that I am unwell and unable to attend work due to illness. I have consulted with my doctor who has advised me to take rest for a few days.

I would like to request sick leave from [Start Date] to [End Date]. I will ensure that all my pending work is completed upon my return, and I will coordinate with my team members to handle any urgent matters during my absence.

I have attached my medical certificate for your reference. Please let me know if you need any additional documentation.

Thank you for your understanding.

Yours sincerely,
[Your Name]
[Your Employee ID]
[Your Contact Information]"""
        
        # Save to file
        filename = f"Data/sick_leave_letter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        os.makedirs("Data", exist_ok=True)
        
        with open(filename, "w", encoding="utf-8") as file:
            file.write(letter)
        
        # Open in notepad
        try:
            subprocess.Popen(['notepad.exe', filename])
        except Exception as e:
            logger.warning(f"Could not open notepad: {e}")
            print(f"Letter saved to: {filename}")
        
        print("Generated Sick Leave Letter:")
        print("="*50)
        print(letter)
        return True
        
    except Exception as e:
        logger.error(f"Error generating sick leave letter: {e}")
        return False

def Content(Topic):
    """Generate content using AI and save it to a file"""
    
    def OpenNotepad(File):
        """Open a file in Notepad"""
        try:
            default_text_editor = 'notepad.exe'
            subprocess.Popen([default_text_editor, File])
        except Exception as e:
            logger.error(f"Error opening notepad: {e}")

    def ContentWriterAI(prompt):
        """Generate content using the AI chatbot"""
        try:
            messages.append({"role": "user", "content": f"{prompt}"})

            completion = Client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=SystemChatBot + messages,
                max_tokens=2048,
                temperature=0.7,
                top_p=1,
                stream=True,
                stop=None
            )

            Answer = ""
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    Answer += chunk.choices[0].delta.content

            Answer = Answer.replace("</s>", "")
            messages.append({"role": "assistant", "content": Answer})
            return Answer
            
        except Exception as e:
            logger.error(f"Error in AI content generation: {e}")
            return "Sorry, I couldn't generate the content at this time."
    
    try:
        logger.info(f"Generating content for: {Topic}")
        Topic_clean = Topic.replace("content", "").strip()
        contentByAI = ContentWriterAI(Topic_clean)

        os.makedirs("Data", exist_ok=True)
        filename = f"Data/{Topic_clean.lower().replace(' ', '_').replace(',', '').replace('.', '')}.txt"
        
        with open(filename, "w", encoding="utf-8") as file:
            file.write(contentByAI)

        OpenNotepad(filename)
        return True
        
    except Exception as e:
        logger.error(f"Error in content generation: {e}")
        return False

def YouTubeSearch(Topic):
    """Search YouTube for the given topic"""
    try:
        logger.info(f"Performing YouTube search for: {Topic}")
        search_url = f"https://www.youtube.com/results?search_query={Topic.replace(' ', '+')}"
        webbrowser.open(search_url)
        return True
    except Exception as e:
        logger.error(f"Error in YouTube search: {e}")
        return False

def PlayYoutube(query):
    """Play a video on YouTube"""
    try:
        logger.info(f"Playing on YouTube: {query}")
        playonyt(query)
        return True
    except Exception as e:
        logger.error(f"Error playing YouTube video: {e}")
        # Fallback to YouTube search
        return YouTubeSearch(query)

def OpenApp(app):
    """
    Enhanced app opening function with comprehensive URL mapping and error handling
    """
    try:
        # First try to open the app locally
        logger.info(f"Attempting to open {app} locally")
        appopen(app, match_closest=True, output=True, throw_error=True)
        logger.info(f"Successfully opened {app} locally")
        return True
    
    except Exception as e:
        logger.info(f"App '{app}' not found locally, trying web alternatives")
        
        # Comprehensive direct URLs mapping
        direct_urls = {
            # Social Media & Communication
            'whatsapp': 'https://web.whatsapp.com',
            'whatsapp web': 'https://web.whatsapp.com',
            'telegram': 'https://web.telegram.org',
            'discord': 'https://discord.com/app',
            'slack': 'https://app.slack.com',
            'teams': 'https://teams.microsoft.com',
            'microsoft teams': 'https://teams.microsoft.com',
            'zoom': 'https://zoom.us/join',
            'skype': 'https://web.skype.com',
            
            # Social Networks
            'facebook': 'https://www.facebook.com',
            'instagram': 'https://www.instagram.com',
            'twitter': 'https://www.twitter.com',
            'x': 'https://www.x.com',
            'linkedin': 'https://www.linkedin.com',
            'tiktok': 'https://www.tiktok.com',
            'snapchat': 'https://web.snapchat.com',
            'pinterest': 'https://www.pinterest.com',
            
            # Google Services
            'gmail': 'https://mail.google.com',
            'google': 'https://www.google.com',
            'google drive': 'https://drive.google.com',
            'drive': 'https://drive.google.com',
            'google docs': 'https://docs.google.com',
            'docs': 'https://docs.google.com',
            'google sheets': 'https://sheets.google.com',
            'sheets': 'https://sheets.google.com',
            'google slides': 'https://slides.google.com',
            'slides': 'https://slides.google.com',
            'youtube': 'https://www.youtube.com',
            'google calendar': 'https://calendar.google.com',
            'calendar': 'https://calendar.google.com',
            'google photos': 'https://photos.google.com',
            'photos': 'https://photos.google.com',
            'google maps': 'https://maps.google.com',
            'maps': 'https://maps.google.com',
            
            # Microsoft Services
            'outlook': 'https://outlook.live.com',
            'onedrive': 'https://onedrive.live.com',
            'office': 'https://office.com',
            'word': 'https://office.com/word',
            'excel': 'https://office.com/excel',
            'powerpoint': 'https://office.com/powerpoint',
            
            # Entertainment
            'netflix': 'https://www.netflix.com',
            'amazon prime': 'https://www.primevideo.com',
            'prime video': 'https://www.primevideo.com',
            'disney plus': 'https://www.disneyplus.com',
            'disney+': 'https://www.disneyplus.com',
            'hulu': 'https://www.hulu.com',
            'spotify': 'https://open.spotify.com',
            'apple music': 'https://music.apple.com',
            'amazon music': 'https://music.amazon.com',
            'youtube music': 'https://music.youtube.com',
            
            # Shopping & Services
            'amazon': 'https://www.amazon.com',
            'ebay': 'https://www.ebay.com',
            'flipkart': 'https://www.flipkart.com',
            'paytm': 'https://paytm.com',
            'gpay': 'https://pay.google.com',
            'google pay': 'https://pay.google.com',
            'phonepe': 'https://www.phonepe.com',
            'paypal': 'https://www.paypal.com',
            
            # Professional & Development
            'github': 'https://github.com',
            'stackoverflow': 'https://stackoverflow.com',
            'stack overflow': 'https://stackoverflow.com',
            'figma': 'https://www.figma.com',
            'canva': 'https://www.canva.com',
            'notion': 'https://www.notion.so',
            'trello': 'https://trello.com',
            'asana': 'https://app.asana.com',
            'jira': 'https://www.atlassian.com/software/jira',
            
            # News & Information
            'reddit': 'https://www.reddit.com',
            'wikipedia': 'https://www.wikipedia.org',
            'medium': 'https://medium.com',
            'quora': 'https://www.quora.com',
            
            # Indian Services
            'swiggy': 'https://www.swiggy.com',
            'zomato': 'https://www.zomato.com',
            'ola': 'https://book.olacabs.com',
            'uber': 'https://www.uber.com',
            'myntra': 'https://www.myntra.com',
            'nykaa': 'https://www.nykaa.com',
            
            # Banking & Finance
            'sbi': 'https://www.onlinesbi.sbi',
            'hdfc': 'https://netbanking.hdfcbank.com',
            'icici': 'https://www.icicibank.com',
            'axis': 'https://www.axisbank.com',
        }
        
        # Normalize app name for comparison
        app_lower = app.strip().lower()
        
        # Check for exact matches first
        if app_lower in direct_urls:
            logger.info(f"Opening {app} via direct URL: {direct_urls[app_lower]}")
            webopen(direct_urls[app_lower])
            return True
        
        # Check for partial matches
        for key, url in direct_urls.items():
            if key in app_lower or any(word in app_lower for word in key.split()):
                logger.info(f"Opening {app} via partial match ({key}): {url}")
                webopen(url)
                return True
        
        # Try constructed URLs for unknown apps
        constructed_urls = [
            f"https://www.{app_lower.replace(' ', '')}.com",
            f"https://{app_lower.replace(' ', '')}.com",
            f"https://app.{app_lower.replace(' ', '')}.com",
            f"https://web.{app_lower.replace(' ', '')}.com"
        ]
        
        logger.info(f"Trying constructed URL: {constructed_urls[0]}")
        webopen(constructed_urls[0])
        return True

def CloseApp(app):
    """Close an application"""
    try:
        if "chrome" in app.lower():
            logger.info("Chrome close command ignored for safety")
            return True
        else:
            logger.info(f"Attempting to close: {app}")
            close(app, match_closest=True, output=True, throw_error=True)
            return True
    except Exception as e:
        logger.error(f"Error closing {app}: {e}")
        return False

def System(command):
    """Handle system commands like volume control"""
    
    def mute():
        keyboard.press_and_release("volume mute")
       
    def unmute():
        keyboard.press_and_release("volume mute")
       
    def volume_up():
        keyboard.press_and_release("volume up")
       
    def volume_down():
        keyboard.press_and_release("volume down")

    try:
        logger.info(f"Executing system command: {command}")
        
        command_lower = command.lower().strip()
        
        if command_lower == "mute":
            mute()
        elif command_lower == "unmute":
            unmute()
        elif command_lower in ["volume up", "increase volume"]:
            volume_up()
        elif command_lower in ["volume down", "decrease volume"]:
            volume_down()
        else:
            logger.warning(f"Unknown system command: {command}")
            return False

        return True
        
    except Exception as e:
        logger.error(f"Error executing system command {command}: {e}")
        return False

async def TranslateAndExecute(commands: list[str]):
    """Process and execute voice commands asynchronously"""
    funcs = []

    for command in commands:
        command = command.strip().lower()
        logger.info(f"Processing command: {command}")
        
        try:
            # Handle sick leave letter specifically
            if "write letter for sick leave" in command or "sick leave letter" in command:
                fun = asyncio.to_thread(generate_sick_leave_letter)
                funcs.append(fun)
                
            elif command.startswith("open "):
                if "open it" in command or "open file" == command:
                    logger.info("Ignoring generic open command")
                    pass
                else:
                    app_name = command.removeprefix("open").strip()
                    fun = asyncio.to_thread(OpenApp, app_name)
                    funcs.append(fun)

            elif command.startswith("close "):
                app_name = command.removeprefix("close").strip()
                fun = asyncio.to_thread(CloseApp, app_name)
                funcs.append(fun)

            elif command.startswith("play "):
                query = command.removeprefix("play").strip()
                fun = asyncio.to_thread(PlayYoutube, query)
                funcs.append(fun)

            elif command.startswith("content "):
                topic = command.removeprefix("content").strip()
                fun = asyncio.to_thread(Content, topic)
                funcs.append(fun)

            elif command.startswith("google search "):
                query = command.removeprefix("google search").strip()
                fun = asyncio.to_thread(GoogleSearch, query)
                funcs.append(fun)

            elif command.startswith("youtube search "):
                query = command.removeprefix("youtube search").strip()
                fun = asyncio.to_thread(YouTubeSearch, query)
                funcs.append(fun)

            elif command.startswith("system "):
                sys_command = command.removeprefix("system").strip()
                fun = asyncio.to_thread(System, sys_command)
                funcs.append(fun)

            else:
                logger.warning(f"No function found for command: '{command}'")

        except Exception as e:
            logger.error(f"Error processing command '{command}': {e}")

    if funcs:
        try:
            results = await asyncio.gather(*funcs, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Task {i} failed with error: {result}")
                elif isinstance(result, str):
                    yield result
                else:
                    yield result
                    
        except Exception as e:
            logger.error(f"Error executing tasks: {e}")

async def Automation(commands: list[str]):
    """Main automation function to handle voice commands"""
    try:
        logger.info(f"Starting automation with commands: {commands}")
        
        async for result in TranslateAndExecute(commands):
            if result:
                logger.info(f"Command executed successfully: {result}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in automation: {e}")
        return False

# Test the automation commands
if __name__ == "__main__":
    # Test various commands
    test_commands = [
        "open whatsapp",
        "play Afsanay",
        "google search python programming",
        "system volume up"
    ]
    
    for cmd in test_commands:
        print(f"\nTesting command: {cmd}")
        asyncio.run(Automation([cmd]))
        input("Press Enter to continue to next test...")