import os
import openai
import json
from PyQt5.QtWidgets import QApplication, QWidget, QTextEdit, QLineEdit, QVBoxLayout
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

class LLMWorker(QThread):
    result_ready = pyqtSignal(str)  # Signal to emit when the result is ready

    def __init__(self, user_input, openai_client, assistant_openai, thread_openai):
        super().__init__()
        self.user_input = user_input
        self.openai_client = openai_client
        self.assistant_openai = assistant_openai
        self.thread_openai = thread_openai

    def run(self):
        # Send the request to OpenAI
        try:
            # Send user input to OpenAI
            thread_message = self.openai_client.beta.threads.messages.create(
                thread_id=self.thread_openai.id,
                role="user",
                content=self.user_input,
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
                            self.result_ready.emit(message.content[0].text.value)
                            return
            self.result_ready.emit("Error: No response from the assistant.")
        except Exception as e:
            self.result_ready.emit(f"Error: {e}")

class OpenAIChatbot(QWidget):
    def __init__(self):
        super().__init__()

        # Load configuration
        config_file = "config.json"
        with open(config_file, 'r') as file:
            config = json.load(file)

        self.instructions = config['instructions']
        self.model = config['model']
        self.name = config['name']

        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            print("API key is not set. Please set the OPENAI_API_KEY environment variable.")
            exit(1)

        self.client = openai.OpenAI()

        self.assistant = self.client.beta.assistants.create(
            model=self.model,
            instructions=self.instructions,
            name=self.name,
            tools=[{"type": "file_search"}]
        )

        self.thread = self.client.beta.threads.create()

        # Initialize GUI
        self.init_gui()

    def init_gui(self):
        self.setWindowTitle("JuanGPT")
        self.setGeometry(100, 100, 600, 400)
        self.setAcceptDrops(True)  # Enable drag and drop

        layout = QVBoxLayout()

        # Create text area for displaying messages
        self.text_area = QTextEdit(self)
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)

        # Display assistant and thread IDs
        self.text_area.append(f"Assistant ID: {self.assistant.id}")
        self.text_area.append(f"Thread ID: {self.thread.id}")

        # Input area for user messages
        self.user_input = QLineEdit(self)
        self.user_input.setPlaceholderText("Type your message and press Enter")
        layout.addWidget(self.user_input)

        # Connect Enter key to input processing
        self.user_input.returnPressed.connect(self.on_enter_pressed)

        # Set layout
        self.setLayout(layout)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.upload_file(file_path)

    def upload_file(self, file_path):
        try:
            with open(file_path, 'rb') as file_data:
                file_object = self.client.files.create(
                    file=file_data,
                    purpose='assistants'
                )
            self.text_area.append(f"File uploaded successfully: ID {file_object.id}")
            # Attach the file to the thread
            try:
                self.client.beta.threads.messages.create(
                    thread_id=self.thread.id,
                    role="user",
                    content="File uploaded.",
                    attachments=[{"file_id": file_object.id, "tools": [{"type": "file_search"}]}]
                )
            except Exception as e:
                self.text_area.append(f"Failed to attach file to thread: {e}")
            self.text_area.append(">>>>>>>>>>>>>>>>>>>>>>>>>>")
        except Exception as e:
            self.text_area.append(f"Failed to upload file: {e}")

    def on_enter_pressed(self):
        user_input = self.user_input.text().strip()
        if user_input:
            self.process_user_input(user_input)
        self.user_input.clear()

    def process_user_input(self, user_input):
        self.text_area.append(f"Juan: {user_input}")
        self.text_area.append(">>>>>>>>>>>>>>>>>>>>>>>>>>")

        # Disable the input field during processing
        self.user_input.setEnabled(False)

        # Start the worker thread
        self.worker_thread = LLMWorker(
            user_input, self.client, self.assistant, self.thread
        )
        self.worker_thread.result_ready.connect(self.display_results)
        self.worker_thread.start()

    def display_results(self, response):
        self.text_area.append(f"{self.name}: {response}")
        self.text_area.append("<<<<<<<<<<<<<<<<<<<<<<<<<<")

        # Re-enable the input field after processing is done
        self.user_input.setEnabled(True)

if __name__ == "__main__":
    app = QApplication([])
    chatbot = OpenAIChatbot()
    chatbot.show()
    app.exec_()
