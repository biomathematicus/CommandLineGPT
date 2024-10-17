import os
import anthropic
import PyPDF2
from PyQt5.QtWidgets import QApplication, QWidget, QTextEdit, QLineEdit, QVBoxLayout
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

class ClaudeWorker(QThread):
    result_ready = pyqtSignal(str)  # Signal to emit when the result is ready

    def __init__(self, user_input, messages, anthropic_client):
        super().__init__()
        self.user_input = user_input
        self.messages = messages
        self.anthropic_client = anthropic_client

    def run(self):
        # Send the request to Claude
        try:
            # Add user input to the conversation
            self.messages.append({"role": "user", "content": self.user_input})

            # Send the message to Claude and get the response
            response = self.anthropic_client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                temperature=0.99,
                messages=self.messages
            )
            assistant_message = response.content[0].text
            self.messages.append({"role": "assistant", "content": assistant_message})

            self.result_ready.emit(assistant_message)
        except Exception as e:
            self.result_ready.emit(f"Error: {e}")

class ClaudeChatbot(QWidget):
    def __init__(self):
        super().__init__()

        # Initialize Anthropic API client
        apiKey = os.getenv("ANTHROPIC_API_KEY")
        if not apiKey:
            print("Anthropic API key is not set. Please set the ANTHROPIC_API_KEY environment variable.")
            exit(1)
        
        self.client = anthropic.Anthropic(api_key=apiKey)
        self.messages = []  # Store the conversation messages

        # Initialize GUI
        self.init_gui()

    def init_gui(self):
        self.setWindowTitle("ClaudeGPT")
        self.setGeometry(100, 100, 600, 400)
        self.setAcceptDrops(True)  # Enable drag and drop

        layout = QVBoxLayout()

        # Create text area for displaying messages
        self.text_area = QTextEdit(self)
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)

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
            if not file_path.lower().endswith('.pdf'):
                self.text_area.append(f"Error: Only PDF files are supported.")
                return

            pdf_text = self.extract_text_from_pdf(file_path)
            user_message = f"I've uploaded a PDF file. Here's the content:\n\n{pdf_text}\n\nPlease analyze this PDF content."
            self.messages.append({"role": "user", "content": user_message})
            self.text_area.append(f"PDF '{file_path}' uploaded and processed successfully.")
            self.text_area.append(">>>>>>>>>>>>>>>>>>>>>>>>>>")
            self.process_user_input(user_message)  # Automatically send the PDF content for analysis
        except Exception as e:
            self.text_area.append(f"Failed to upload file: {e}")

    def extract_text_from_pdf(self, file_path):
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text

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
        self.worker_thread = ClaudeWorker(
            user_input, self.messages, self.client
        )
        self.worker_thread.result_ready.connect(self.display_results)
        self.worker_thread.start()

    def display_results(self, response):
        self.text_area.append(f"Claude: {response}")
        self.text_area.append("<<<<<<<<<<<<<<<<<<<<<<<<<<")

        # Re-enable the input field after processing is done
        self.user_input.setEnabled(True)

if __name__ == "__main__":
    app = QApplication([])
    chatbot = ClaudeChatbot()
    chatbot.show()
    app.exec_()
