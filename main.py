"""
Enhanced AI Assistant Main Application
Rewritten for better error handling, code organization, and reliability
"""

from Frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,
    TempDirectoryPath,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus
)

from Backend.Model import classify_input
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import handle_chat
from Backend.TextToSpeech import TextToSpeech
from dotenv import dotenv_values
from asyncio import run
from time import sleep
import subprocess
import threading
import json
import os
import logging
import sys
from pathlib import Path


class AIAssistantCore:
    """Core AI Assistant functionality"""
    
    def __init__(self):
        self.setup_logging()
        self.load_configuration()
        self.active_subprocesses = []
        self.running = True
        
    def setup_logging(self):
        """Setup comprehensive logging"""
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('ai_assistant.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_configuration(self):
        """Load environment variables and configuration"""
        try:
            env_vars = dotenv_values(".env")
            self.username = env_vars.get("Username", "User")
            self.assistant_name = env_vars.get("Assistantname", "Friday")
            self.logger.info(f"Configuration loaded - Username: {self.username}, Assistant: {self.assistant_name}")
        except Exception as e:
            self.logger.error(f"Error loading .env file: {e}")
            self.username = "User"
            self.assistant_name = "Friday"
            
        self.default_message = f'''{self.username}: Hello {self.assistant_name}, how are you?
{self.assistant_name}: Welcome {self.username}. I am doing well. How may I help you?'''

    def ensure_directories_exist(self):
        """Ensure all required directories exist"""
        directories = [
            "Data",
            "Frontend/Files",
            "Backend",
            Path(TempDirectoryPath("")).parent
        ]
        
        for directory in directories:
            try:
                Path(directory).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self.logger.error(f"Error creating directory {directory}: {e}")

    def initialize_default_chat(self):
        """Initialize default chat if no existing chats found"""
        try:
            chatlog_path = Path("Data/ChatLog.json")
            
            if not chatlog_path.exists() or chatlog_path.stat().st_size < 5:
                self.logger.info("Initializing default chat")
                
                # Create empty database
                with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
                    file.write("")
                
                # Create default response
                with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as file:
                    file.write(self.default_message)
                    
        except Exception as e:
            self.logger.error(f"Error initializing default chat: {e}")

    def read_chat_log(self):
        """Read and return chat log data with error handling"""
        try:
            with open("Data/ChatLog.json", "r", encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            self.logger.warning("ChatLog.json not found, returning empty list")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing ChatLog.json: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error reading chat log: {e}")
            return []

    def integrate_chat_log(self):
        """Integrate chat log data with the database"""
        try:
            json_data = self.read_chat_log()
            if not json_data:
                return
                
            formatted_chatlog = ""
            
            for entry in json_data:
                if not isinstance(entry, dict):
                    continue
                    
                role = entry.get("role", "")
                content = entry.get("content", "")
                
                if role == "user":
                    formatted_chatlog += f"{self.username}: {content}\n"
                elif role == "assistant":
                    formatted_chatlog += f"{self.assistant_name}: {content}\n"
            
            if formatted_chatlog:
                with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
                    file.write(AnswerModifier(formatted_chatlog))
                    
        except Exception as e:
            self.logger.error(f"Error integrating chat log: {e}")

    def update_gui_display(self):
        """Update GUI with current chat data"""
        try:
            database_path = TempDirectoryPath('Database.data')
            
            if Path(database_path).exists():
                with open(database_path, "r", encoding='utf-8') as file:
                    data = file.read().strip()
                    
                if data:
                    with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as file:
                        file.write(data)
                        
        except Exception as e:
            self.logger.error(f"Error updating GUI display: {e}")

    def classify_command(self, query):
        """Enhanced command classification with better keyword matching"""
        query_lower = query.lower().strip()
        
        # Image generation detection
        image_keywords = [
            "generate image", "create image", "make image", "draw", 
            "generate picture", "create picture", "make picture",
            "generate photo", "create photo", "make photo",
            "image of", "picture of", "photo of"
        ]
        
        if any(keyword in query_lower for keyword in image_keywords):
            self.logger.info(f"Image generation command detected: {query}")
            return "image_generation", query
        
        # Realtime search detection
        search_keywords = [
            "search", "google", "find", "look up", "search for",
            "what is", "who is", "when is", "where is", "how is",
            "current", "latest", "news", "weather", "today"
        ]
        
        if any(keyword in query_lower for keyword in search_keywords):
            self.logger.info(f"Search command detected: {query}")
            return "realtime_search", query
        
        # Automation detection
        automation_keywords = [
            "open", "close", "play", "stop", "start", "launch",
            "system", "application", "program", "file", "folder"
        ]
        
        if any(keyword in query_lower for keyword in automation_keywords):
            self.logger.info(f"Automation command detected: {query}")
            return "automation", query
        
        # Exit detection
        exit_keywords = ["exit", "quit", "goodbye", "bye", "stop", "shut down"]
        
        if any(keyword in query_lower for keyword in exit_keywords):
            self.logger.info(f"Exit command detected: {query}")
            return "exit", query
        
        # Default to general chat
        self.logger.info(f"General chat command detected: {query}")
        return "general", query

    def handle_image_generation(self, query):
        """Handle image generation with improved error handling"""
        try:
            self.logger.info(f"Starting image generation for: {query}")
            SetAssistantStatus("Preparing image generation...")
            
            # Ensure directory exists
            image_data_dir = Path("Frontend/Files")
            image_data_dir.mkdir(parents=True, exist_ok=True)
            
            # Clean the query - remove trailing punctuation
            cleaned_query = query.strip().rstrip('.,!?;:')
            
            # Write properly formatted data
            image_data_file = image_data_dir / "ImageGeneration.data"
            with open(image_data_file, "w", encoding='utf-8') as file:
                file.write(f"{cleaned_query}, True")
            
            self.logger.info(f"Image data written: '{cleaned_query}, True'")
            
            # Start image generation process
            process = subprocess.Popen(
                [sys.executable, "Backend/ImageGeneration.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.getcwd()
            )
            
            self.active_subprocesses.append(process)
            
            response = "I'm generating the image for you. Please wait a moment while I create it."
            ShowTextToScreen(f"{self.assistant_name}: {response}")
            SetAssistantStatus("Generating Image...")
            TextToSpeech(response)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in image generation: {e}")
            error_response = "I'm sorry, I encountered an error while trying to generate the image. Please try again."
            ShowTextToScreen(f"{self.assistant_name}: {error_response}")
            SetAssistantStatus("Image generation failed")
            TextToSpeech(error_response)
            return False

    def handle_realtime_search(self, query):
        """Handle realtime search with fallback"""
        try:
            SetAssistantStatus("Searching...")
            modified_query = QueryModifier(query)
            answer = RealtimeSearchEngine(modified_query)
            
            ShowTextToScreen(f"{self.assistant_name}: {answer}")
            SetAssistantStatus("Answering...")
            TextToSpeech(answer)
            return True
            
        except Exception as e:
            self.logger.error(f"Error in realtime search: {e}")
            try:
                # Fallback to general chat
                SetAssistantStatus("Searching failed, using general knowledge...")
                answer = handle_chat(QueryModifier(query))
                ShowTextToScreen(f"{self.assistant_name}: {answer}")
                SetAssistantStatus("Answering...")
                TextToSpeech(answer)
                return True
            except Exception as fallback_error:
                self.logger.error(f"Fallback also failed: {fallback_error}")
                return False

    def handle_automation(self, query):
        """Handle automation tasks"""
        try:
            SetAssistantStatus("Processing automation...")
            decision = classify_input(query)
            
            if decision and isinstance(decision, list):
                run(Automation(decision))
                response = "Task completed successfully."
            else:
                response = "I'm not sure how to perform that automation task. Could you be more specific?"
            
            ShowTextToScreen(f"{self.assistant_name}: {response}")
            SetAssistantStatus("Task completed")
            TextToSpeech(response)
            return True
            
        except Exception as e:
            self.logger.error(f"Error in automation: {e}")
            error_response = "I encountered an error while trying to perform that task."
            ShowTextToScreen(f"{self.assistant_name}: {error_response}")
            SetAssistantStatus("Automation failed")
            TextToSpeech(error_response)
            return False

    def handle_general_chat(self, query):
        """Handle general conversation"""
        try:
            SetAssistantStatus("Thinking...")
            modified_query = QueryModifier(query)
            answer = handle_chat(modified_query)
            
            ShowTextToScreen(f"{self.assistant_name}: {answer}")
            SetAssistantStatus("Answering...")
            TextToSpeech(answer)
            return True
            
        except Exception as e:
            self.logger.error(f"Error in general chat: {e}")
            error_response = "I'm having trouble processing that. Could you please try again?"
            ShowTextToScreen(f"{self.assistant_name}: {error_response}")
            TextToSpeech(error_response)
            return False

    def process_user_input(self):
        """Main input processing logic"""
        try:
            # Get voice input
            SetAssistantStatus("Listening...")
            query = SpeechRecognition()
            
            if not query or not query.strip():
                self.logger.warning("Empty or invalid query received")
                SetAssistantStatus("Available...")
                return True
            
            self.logger.info(f"Processing query: '{query}'")
            ShowTextToScreen(f"{self.username}: {query}")
            SetAssistantStatus("Processing...")
            
            # Classify and handle the command
            command_type, processed_query = self.classify_command(query)
            
            # Route to appropriate handler
            handlers = {
                "image_generation": self.handle_image_generation,
                "realtime_search": self.handle_realtime_search,
                "automation": self.handle_automation,
                "general": self.handle_general_chat,
                "exit": lambda q: False  # Return False to exit
            }
            
            handler = handlers.get(command_type, self.handle_general_chat)
            result = handler(processed_query)
            
            if command_type == "exit":
                goodbye_response = handle_chat(QueryModifier("Goodbye! Have a great day!"))
                ShowTextToScreen(f"{self.assistant_name}: {goodbye_response}")
                TextToSpeech(goodbye_response)
                return False
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing user input: {e}")
            try:
                error_response = "I encountered an error. How else can I help you?"
                ShowTextToScreen(f"{self.assistant_name}: {error_response}")
                SetAssistantStatus("Error occurred")
                TextToSpeech(error_response)
            except:
                pass
            return True

    def main_processing_loop(self):
        """Main processing thread loop"""
        self.logger.info("Starting main processing loop")
        
        while self.running:
            try:
                microphone_status = GetMicrophoneStatus()
                
                if microphone_status == "True":
                    should_continue = self.process_user_input()
                    if not should_continue:
                        self.logger.info("Exit command received, stopping application")
                        self.running = False
                        break
                else:
                    # Update status if needed
                    current_status = GetAssistantStatus()
                    if "Available..." not in current_status:
                        SetAssistantStatus("Available...")
                    sleep(0.1)
                    
            except Exception as e:
                self.logger.error(f"Error in main processing loop: {e}")
                sleep(1)

    def gui_thread(self):
        """GUI thread wrapper"""
        self.logger.info("Starting GUI thread")
        try:
            GraphicalUserInterface()
        except Exception as e:
            self.logger.error(f"Error in GUI thread: {e}")
            self.running = False

    def cleanup(self):
        """Clean up resources and subprocesses"""
        self.logger.info("Cleaning up resources...")
        
        for process in self.active_subprocesses:
            try:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)
            except Exception as e:
                self.logger.error(f"Error terminating process: {e}")
                try:
                    process.kill()
                except:
                    pass

    def initialize(self):
        """Initialize the application"""
        self.logger.info("Initializing AI Assistant...")
        
        try:
            # Setup environment
            self.ensure_directories_exist()
            SetMicrophoneStatus("false")
            ShowTextToScreen("")
            
            # Initialize chat system
            self.initialize_default_chat()
            self.integrate_chat_log()
            self.update_gui_display()
            
            self.logger.info("AI Assistant initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during initialization: {e}")
            return False

    def run(self):
        """Main application entry point"""
        try:
            # Initialize the application
            if not self.initialize():
                self.logger.error("Failed to initialize application")
                return
            
            # Start the main processing thread
            main_thread = threading.Thread(target=self.main_processing_loop, daemon=True)
            main_thread.start()
            
            # Run the GUI (blocking)
            self.gui_thread()
            
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
        except Exception as e:
            self.logger.error(f"Unexpected error in main application: {e}")
        finally:
            self.running = False
            self.cleanup()
            self.logger.info("AI Assistant shutdown complete")


def main():
    """Application entry point"""
    assistant = AIAssistantCore()
    assistant.run()


if __name__ == "__main__":
    main()