import os
import openai
import anthropic
import json
from PyQt5.QtWidgets import QApplication, QWidget, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# Worker thread for processing LLM responses
class LLMWorker(QThread):
    result_ready = pyqtSignal(str, str)  # Signal to emit when the result is ready

    def __init__(self, modelLeft, modelRight, user_input, openai_client, assistant_openai, thread_openai, anthropic_client):
        super().__init__()
        self.modelLeft = modelLeft
        self.modelRight = modelRight
        self.user_input = user_input
        self.openai_client = openai_client
        self.assistant_openai = assistant_openai
        self.thread_openai = thread_openai
        self.anthropic_client = anthropic_client

    def run(self):
        # Send requests to OpenAI and Anthropic in parallel
        response_left = self.send_to_openai(self.user_input)
        response_right = self.send_to_anthropic(self.user_input)

        # Emit the signal when both responses are ready
        self.result_ready.emit(response_left, response_right)

    def send_to_openai(self, user_input):
        try:
            thread_message = self.openai_client.beta.threads.messages.create(
                thread_id=self.thread_openai.id,
                role="user",
                content=user_input,
            )
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

# Main Chatbot Class
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
        self.last_improved_left = None  # OpenAI last improved response
        self.last_improved_right = None  # Anthropic last improved response

        # Initialize GUI
        self.init_gui()

    def init_gui(self):
        self.setWindowTitle("Multi-LLM Chatbot")
        self.setGeometry(100, 100, 1000, 600)

        layout = QVBoxLayout()

        # Create horizontal layout for side by side text areas
        text_area_layout = QHBoxLayout()

        # Text area for OpenAI responses
        self.text_area_left = QTextEdit()
        self.text_area_left.setPlaceholderText("OpenAI Response")
        self.text_area_left.setReadOnly(True)
        text_area_layout.addWidget(self.text_area_left)

        # Text area for Anthropic responses
        self.text_area_right = QTextEdit()
        self.text_area_right.setPlaceholderText("Anthropic Response")
        self.text_area_right.setReadOnly(True)
        text_area_layout.addWidget(self.text_area_right)

        layout.addLayout(text_area_layout)

        # Copy buttons
        copy_button_layout = QHBoxLayout()

        self.copy_button_left = QPushButton("Copy OpenAI Response")
        self.copy_button_left.clicked.connect(self.copy_openai_response)
        copy_button_layout.addWidget(self.copy_button_left)

        self.copy_button_right = QPushButton("Copy Anthropic Response")
        self.copy_button_right.clicked.connect(self.copy_anthropic_response)
        copy_button_layout.addWidget(self.copy_button_right)

        layout.addLayout(copy_button_layout)

        # Loading indicator
        self.loading_label = QLabel("")
        layout.addWidget(self.loading_label)

        # User input field
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Type your input here and press Enter")
        layout.addWidget(self.user_input)

        self.setLayout(layout)

        # Connect Enter key to input processing
        self.user_input.returnPressed.connect(self.on_enter_pressed)

    def copy_openai_response(self):
        response_to_copy = self.last_improved_left if self.last_improved_left else self.last_response_left
        if response_to_copy:
            clipboard = QApplication.clipboard()
            clipboard.setText(response_to_copy)

    def copy_anthropic_response(self):
        response_to_copy = self.last_improved_right if self.last_improved_right else self.last_response_right
        if response_to_copy:
            clipboard = QApplication.clipboard()
            clipboard.setText(response_to_copy)

    def on_enter_pressed(self):
        user_input = self.user_input.text().strip()
        if user_input:
            if user_input.upper() == "FOO":
                self.criticize_each_other()
            else:
                self.process_user_input(user_input)
        self.user_input.clear()

    def process_user_input(self, user_input):
        # Reset improved responses (since a normal query is being made)
        self.last_improved_left = None
        self.last_improved_right = None

        # Display user input first, followed by the line of characters
        self.text_area_left.append(">>>>>>>>>>>>>>>>>>>>>>>>>>")
        self.text_area_left.append(f"User: {user_input}")
        self.text_area_left.append("--------------------")
        self.text_area_right.append(">>>>>>>>>>>>>>>>>>>>>>>>>>")
        self.text_area_right.append(f"User: {user_input}")
        self.text_area_right.append("--------------------")

        # Show loading indicator
        self.loading_label.setText("Processing...")

        # Disable the input field to prevent multiple inputs
        self.user_input.setEnabled(False)

        # Create and start the background thread
        self.user_input_thread = LLMWorker(
            self.modelLeft, self.modelRight, user_input, self.openai_client,
            self.assistant_openai, self.thread_openai, self.anthropic_client
        )
        self.user_input_thread.result_ready.connect(self.display_results)
        self.user_input_thread.start()

    def display_results(self, response_left, response_right):
        # Store the responses
        self.last_response_left = response_left
        self.last_response_right = response_right

        # Remove loading indicator
        self.loading_label.setText("")

        # Re-enable the input field
        self.user_input.setEnabled(True)

        # Display the responses in the respective text areas, followed by the line of characters
        self.text_area_left.append("<<<<<<<<<<<<<<<<<<<<<<<<<")
        self.text_area_left.append(f"{self.nameLeft}: {response_left}")
        self.text_area_left.append("--------------------")

        self.text_area_right.append("<<<<<<<<<<<<<<<<<<<<<<<<<")
        self.text_area_right.append(f"{self.nameRight}: {response_right}")
        self.text_area_right.append("--------------------")

    def criticize_each_other(self):
        # Show loading indicator
        self.loading_label.setText("Processing critiques...")

        # Disable input field
        self.user_input.setEnabled(False)

        if self.last_response_left is None or self.last_response_right is None:
            self.text_area_left.append("No previous responses to critique.")
            self.text_area_right.append("No previous responses to critique.")
            return

        # Critique LLM responses
        critique_input_left = f"Other LLM responded to the same question as follows. Validate accuracy and find flaws: {self.last_response_right}"
        critique_input_right = f"Other LLM responded to the same question as follows. Validate accuracy and find flaws: {self.last_response_left}"

        # Create and start a separate thread for the critique
        self.critique_thread = LLMWorker(
            self.modelLeft, self.modelRight, critique_input_left, self.openai_client,
            self.assistant_openai, self.thread_openai, self.anthropic_client
        )
        self.critique_thread.result_ready.connect(self.display_critique_results)
        self.critique_thread.start()

    def display_critique_results(self, critique_left, critique_right):
        # Display the critique responses in the respective text areas
        self.text_area_left.append(">-<->-<->-<->-<")
        self.text_area_left.append(f"{self.nameLeft} Critique: {critique_left}")
        self.text_area_left.append("--------------------")
        self.text_area_right.append(">-<->-<->-<->-<")
        self.text_area_right.append(f"{self.nameRight} Critique: {critique_right}")
        self.text_area_right.append("--------------------")

        # Send back critiques for improvement
        improvement_input_left = f"Claude criticized your output as follows. Validate accuracy of the critique and improve your answer. Offer a fresh and detailed answer with all necessary improvements: {critique_right}"
        improvement_input_right = f"GPT criticized your output as follows. Validate accuracy of the critique and improve your answer. Offer a fresh and detailed answer with all necessary improvements: {critique_left}"

        # Process improvements in another thread
        self.improvement_thread = LLMWorker(
            self.modelLeft, self.modelRight, improvement_input_left, self.openai_client,
            self.assistant_openai, self.thread_openai, self.anthropic_client
        )
        self.improvement_thread.result_ready.connect(self.display_improved_results)
        self.improvement_thread.start()

    def display_improved_results(self, improved_left, improved_right):
        # Store the improved responses
        self.last_improved_left = improved_left
        self.last_improved_right = improved_right

        # Display the improved responses in the respective text areas
        self.text_area_left.append(">-<->-<->-<->-<")
        self.text_area_left.append(f"{self.nameLeft} Improved: {improved_left}")
        self.text_area_left.append("--------------------")
        self.text_area_right.append(">-<->-<->-<->-<")
        self.text_area_right.append(f"{self.nameRight} Improved: {improved_right}")
        self.text_area_right.append("--------------------")

        # Remove loading indicator
        self.loading_label.setText("")

        # Re-enable the input field
        self.user_input.setEnabled(True)


if __name__ == "__main__":
    app = QApplication([])
    chatbot = MultiLLMChatbot()
    chatbot.show()
    app.exec_()
