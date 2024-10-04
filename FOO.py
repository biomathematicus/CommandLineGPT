import os
import openai
import anthropic
import json
from PyQt5.QtWidgets import QApplication, QWidget, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit
from PyQt5.QtCore import Qt

class MultiLLMChatbot(QWidget):
    def __init__(self):
        super().__init__()

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

        # Initialize OpenAI API
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
        self.setWindowTitle("Multi-LLM Chatbot")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        # Text areas for OpenAI and Anthropic responses
        self.text_area_left = QTextEdit()
        self.text_area_left.setPlaceholderText("OpenAI Response")
        self.text_area_left.setReadOnly(True)
        layout.addWidget(self.text_area_left)

        self.text_area_right = QTextEdit()
        self.text_area_right.setPlaceholderText("Anthropic Response")
        self.text_area_right.setReadOnly(True)
        layout.addWidget(self.text_area_right)

        # User input field
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Type your input here and press Enter")
        layout.addWidget(self.user_input)

        # Copy buttons
        buttons_layout = QHBoxLayout()
        self.copy_button_left = QPushButton("Copy OpenAI Response")
        self.copy_button_left.clicked.connect(self.copy_openai_response)
        buttons_layout.addWidget(self.copy_button_left)

        self.copy_button_right = QPushButton("Copy Anthropic Response")
        self.copy_button_right.clicked.connect(self.copy_anthropic_response)
        buttons_layout.addWidget(self.copy_button_right)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)

        # Connect Enter key to input processing
        self.user_input.returnPressed.connect(self.on_enter_pressed)

    def copy_openai_response(self):
        if self.last_response_left:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.last_response_left)

    def copy_anthropic_response(self):
        if self.last_response_right:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.last_response_right)

    def on_enter_pressed(self):
        user_input = self.user_input.text().strip()
        if user_input:
            if user_input.upper() == "FOO":
                self.criticize_each_other()
            else:
                self.process_user_input(user_input)
        self.user_input.clear()

    def process_user_input(self, user_input):
        self.text_area_left.append(">>>>>>>>>>>>>>>>>>>>>>>>>>")
        self.text_area_left.append(f"User: {user_input}")
        self.text_area_right.append(">>>>>>>>>>>>>>>>>>>>>>>>>>")
        self.text_area_right.append(f"User: {user_input}")

        # Send user input to both LLMs
        response_left = self.send_to_openai(user_input)
        response_right = self.send_to_anthropic(user_input)

        # Store the responses
        self.last_response_left = response_left
        self.last_response_right = response_right

        # Display the responses in the respective text areas
        self.text_area_left.append(f"{self.nameLeft}: {response_left}")
        self.text_area_left.append("--------------------")

        self.text_area_right.append(f"{self.nameRight}: {response_right}")
        self.text_area_right.append("--------------------")

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
        if self.last_response_left is None or self.last_response_right is None:
            self.text_area_left.append("No previous responses to critique.")
            self.text_area_right.append("No previous responses to critique.")
            return

        critique_left = self.send_to_openai(f"Other LLM responded to the same question as follows. Validate accuracy and find flaws: {self.last_response_right}")
        critique_right = self.send_to_anthropic(f"Other LLM responded to the same question as follows. Validate accuracy and find flaws: {self.last_response_left}")

        self.text_area_left.append(f"{self.nameLeft} Critique: {critique_left}")
        self.text_area_right.append(f"{self.nameRight} Critique: {critique_right}")

        improved_left = self.send_to_openai(f"Other LLM criticized your output as follows. Validate accuracy and improve your answer: {critique_right}")
        improved_right = self.send_to_anthropic(f"Other LLM criticized your output as follows. Validate accuracy and improve your answer: {critique_left}")

        self.text_area_left.append(f"{self.nameLeft} Improved: {improved_left}")
        self.text_area_right.append(f"{self.nameRight} Improved: {improved_right}")

if __name__ == "__main__":
    app = QApplication([])
    chatbot = MultiLLMChatbot()
    chatbot.show()
    app.exec_()
