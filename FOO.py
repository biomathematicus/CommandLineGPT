import os
import openai
import anthropic
import json
import tkinter as tk
from tkinter import scrolledtext, Button

class MultiLLMChatbot:
    def __init__(self):
        # Load configuration
        config_file = "config.json"
        with open(config_file, 'r') as file:
            config = json.load(file)

        self.instructionsLeft = config['instructions']
        self.instructionsRight = config['instructions']
        self.modelLeft = config['modelLeft']
        self.modelRight = config['modelRight']
        self.nameLeft = config['nameLeft']
        self.nameRight = config['nameRight']

        # Initialize OpenAI API (this part remains unchanged)
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            print("OpenAI API key is not set. Please set the OPENAI_API_KEY environment variable.")
            exit(1)

        self.openai_client = openai.OpenAI()

        # Create OpenAI assistant
        self.assistant_openai = self.openai_client.beta.assistants.create(
            model=self.modelLeft,
            instructions=self.instructionsLeft,
            name=self.nameLeft,
            tools=[{"type": "file_search"}]
        )
        
        self.thread_openai = self.openai_client.beta.threads.create()

        # Initialize Anthropic API
        apiKey = os.getenv("ANTHROPIC_API_KEY")
        if not apiKey:
            print("Anthropic API key is not set. Please set the ANTHROPIC_API_KEY environment variable.")
            exit(1)

        self.anthropic_client = anthropic.Anthropic(api_key=apiKey)

        # Keep track of the last responses
        self.last_response_left = None  # OpenAI last response
        self.last_response_right = None  # Anthropic last response

        # Initialize GUI
        self.init_gui()

    def init_gui(self):
        self.root = tk.Tk()
        self.root.title("Multi-LLM Chatbot")

        # Frame to hold the textboxes
        text_frame = tk.Frame(self.root)
        text_frame.pack(expand=True, fill=tk.BOTH)
        
        # Frame to hold the textboxes
        text_frame = tk.Frame(self.root, bg="white")  # Set frame background
        text_frame.pack(expand=True, fill=tk.BOTH)    
    
        # Left textbox for OpenAI responses
        self.text_area_left = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, width=50)
        self.text_area_left.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Button to copy OpenAI response
        self.copy_button_left = Button(self.root, text="Copy OpenAI Response", command=self.copy_openai_response)
        self.copy_button_left.pack(side=tk.LEFT, padx=10, pady=5)

        # Right textbox for Anthropic responses
        self.text_area_right = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, width=50)
        self.text_area_right.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Button to copy Anthropic response
        self.copy_button_right = Button(self.root, text="Copy Anthropic Response", command=self.copy_anthropic_response)
        self.copy_button_right.pack(side=tk.RIGHT, padx=10, pady=5)

        # User input field (spans both text areas)
        self.user_input = tk.Entry(self.root, width=100)
        self.user_input.pack(fill=tk.X, padx=10, pady=10)
        self.user_input.bind("<Return>", self.on_enter_pressed)

        self.root.mainloop()

    def copy_openai_response(self):
        if self.last_response_left:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.last_response_left)
            self.root.update()  # Keeps the clipboard updated

    def copy_anthropic_response(self):
        if self.last_response_right:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.last_response_right)
            self.root.update()  # Keeps the clipboard updated

    def on_enter_pressed(self, event):
        user_input = self.user_input.get().strip()
        if user_input:
            if user_input.upper() == "FOO":
                self.criticize_each_other()  # Trigger critique with previous responses
            else:
                self.process_user_input(user_input)
        self.user_input.delete(0, tk.END)

    def process_user_input(self, user_input):
        self.text_area_left.insert(tk.END, ">>>>>>>>>>>>>>>>>>>>>>>>>>\n")
        self.text_area_left.insert(tk.END, f"User: {user_input}\n")
        self.text_area_right.insert(tk.END, ">>>>>>>>>>>>>>>>>>>>>>>>>>\n")
        self.text_area_right.insert(tk.END, f"User: {user_input}\n")

        # Send user input to both LLMs
        response_left = self.send_to_openai(user_input)
        response_right = self.send_to_anthropic(user_input)

        # Store the responses
        self.last_response_left = response_left
        self.last_response_right = response_right

        # Display the responses in the respective text areas
        self.text_area_left.insert(tk.END, f"Message sent to OpenAI: {user_input}\n")
        self.text_area_left.insert(tk.END, f"{self.nameLeft}: {response_left}\n")
        self.text_area_left.insert(tk.END, "--------------------\n")

        self.text_area_right.insert(tk.END, f"Message sent to Anthropic: {user_input}\n")
        self.text_area_right.insert(tk.END, f"{self.nameRight}: {response_right}\n")
        self.text_area_right.insert(tk.END, "--------------------\n")

    def send_to_openai(self, user_input):
        try:
            # Send message to OpenAI
            thread_message = self.openai_client.beta.threads.messages.create(
                thread_id=self.thread_openai.id,
                role="user",
                content=user_input,
            )
            # Run OpenAI assistant
            run_openai = self.openai_client.beta.threads.runs.create(
                thread_id=self.thread_openai.id,
                assistant_id=self.assistant_openai.id
            )
            # Retrieve responses
            while run_openai.status in ["queued", "in_progress"]:
                run_openai = self.openai_client.beta.threads.runs.retrieve(
                    thread_id=self.thread_openai.id,
                    run_id=run_openai.id
                )
                if run_openai.status == "completed":
                    all_messages = self.openai_client.beta.threads.messages.list(
                        thread_id=self.thread_openai.id
                    )
                    for message in all_messages.data:
                        if message.role == "assistant":
                            return message.content[0].text.value
            return "Error: No response from OpenAI."
        except Exception as e:
            return f"OpenAI error: {e}"

    def send_to_anthropic(self, user_input):
        try:
            # Send message to Claude (Anthropic API)
            response = self.anthropic_client.messages.create(
                model=self.modelRight,
                max_tokens=1000,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": user_input}
                ]
            )
            return response.content[0].text
        except Exception as e:
            return f"Anthropic error: {e}"

    def criticize_each_other(self):
        # Ensure we have previous responses to critique
        if self.last_response_left is None or self.last_response_right is None:
            self.text_area_left.insert(tk.END, "No previous responses to critique.\n")
            self.text_area_right.insert(tk.END, "No previous responses to critique.\n")
            return

        # Step 1: Critique each other's response
        critique_left = self.send_to_openai(f"Other LLM responded to the same question as follows. Validate accuracy and find flaws: {self.last_response_right}")
        critique_right = self.send_to_anthropic(f"Other LLM responded to the same question as follows. Validate accuracy and find flaws: {self.last_response_left}")

        self.text_area_left.insert(tk.END, f"{self.nameLeft} Critique: {critique_left}\n")
        self.text_area_right.insert(tk.END, f"{self.nameRight} Critique: {critique_right}\n")
        self.text_area_left.insert(tk.END, "--------------------\n")
        self.text_area_right.insert(tk.END, "--------------------\n")

        # Step 2: Send back critique for improvement
        improved_left = self.send_to_openai(f"Other LLM criticized your output as follows. Validate accuracy and improve your answer: {critique_right}")
        improved_right = self.send_to_anthropic(f"Other LLM criticized your output as follows. Validate accuracy and improve your answer: {critique_left}")

        self.text_area_left.insert(tk.END, f"{self.nameLeft} Improved: {improved_left}\n")
        self.text_area_right.insert(tk.END, f"{self.nameRight} Improved: {improved_right}\n")
        self.text_area_left.insert(tk.END, "--------------------\n")
        self.text_area_right.insert(tk.END, "--------------------\n")


if __name__ == "__main__":
    MultiLLMChatbot()
