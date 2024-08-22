import os
import openai
import tkinter as tk
from tkinterdnd2 import TkinterDnD, DND_FILES
from tkinter import scrolledtext
import time
import threading
import fitz  # PyMuPDF

# Load the API key from an environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    print("API key is not set. Please set the OPENAI_API_KEY environment variable.")
    exit(1)

client = openai.OpenAI()

# Step 1: Create an Assistant
my_assistant = client.beta.assistants.create(
    model="gpt-4o",
    instructions="""
    Please address the user as Rockin Blonde.
    Information about me: I teach many math courses from baby math to Calculus. I play guitar and have played for years in an alternative rock band. I love learning new things!
    ...
    """,
    name="Vincent Vega, hitman",
    tools=[{"type": "code_interpreter"}],
)

# Create a thread for the conversation
my_thread = client.beta.threads.create()

def send_message():
    user_input = entry.get()
    if not user_input.strip():
        return

    # Add user message to the thread
    client.beta.threads.messages.create(
        thread_id=my_thread.id,
        role="user",
        content=user_input,
    )
    entry.delete(0, tk.END)  # Clear the entry box

    # Disable the send button and start processing
    send_button.config(state=tk.DISABLED)
    status_label.config(text="Processing...")

    # Start a new thread for handling the assistant's response
    threading.Thread(target=process_response).start()

def process_response():
    # Run the assistant
    my_run = client.beta.threads.runs.create(
        thread_id=my_thread.id,
        assistant_id=my_assistant.id
    )

    # Poll for the run status
    while my_run.status in ["queued", "in_progress"]:
        time.sleep(0.5)  # Sleep to prevent too frequent API calls
        keep_retrieving_run = client.beta.threads.runs.retrieve(
            thread_id=my_thread.id,
            run_id=my_run.id
        )
        my_run.status = keep_retrieving_run.status

    if my_run.status == "completed":
        all_messages = client.beta.threads.messages.list(
            thread_id=my_thread.id
        )

        # Extract and display assistant's response
        assistant_response = ""
        for message in all_messages.data:
            if message.role == "assistant":
                assistant_response = message.content[0].text.value
                break

        # Update the GUI with the assistant's response
        update_gui(assistant_response)

def update_gui(response):
    chat_area.config(state=tk.NORMAL)
    chat_area.insert(tk.END, f"Rockin Blonde: {response}\n")
    chat_area.config(state=tk.DISABLED)
    chat_area.yview(tk.END)  # Scroll to the bottom
    status_label.config(text="Ready")
    send_button.config(state=tk.NORMAL)

def handle_dropped_file(file_path):
    # Remove curly braces from the file path
    file_path = file_path.strip('{}')
    
    # Normalize the file path
    file_path = os.path.abspath(file_path)
    print(f"Received file path: {file_path}")  # Debugging line to check the path

    # Extract text from the dropped PDF file
    text = extract_text_from_pdf(file_path)
    if text:
        entry.delete(0, tk.END)  # Clear the entry box
        entry.insert(0, text)  # Insert extracted text
        send_message()  # Automatically send the extracted text
    else:
        update_gui("Error reading the PDF file.")

def extract_text_from_pdf(file_path):
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except fitz.FitzError as e:  # Catch specific PyMuPDF errors
        print(f"PyMuPDF error: {e}")
        return None
    except Exception as e:  # Catch any other exceptions
        print(f"Error reading PDF file: {e}")
        return None

# Set up the GUI
root = TkinterDnD.Tk()  # Use TkinterDnD.Tk instead of tk.Tk
root.title("Chat with Jules")

# Define font styles
font_style = ('Helvetica', 16)  # Font family and size

# Set the window size (width x height)
root.geometry("900x900")  # Example size, adjust as needed

# Create and pack widgets
chat_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, state=tk.DISABLED, height=30, width=80, font=font_style)
chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

entry = tk.Entry(root, width=80, font=font_style)
entry.pack(padx=10, pady=(0, 10), fill=tk.X)

send_button = tk.Button(root, text="Send", command=send_message, font=font_style)
send_button.pack(padx=10, pady=(0, 10))

status_label = tk.Label(root, text="Ready", font=font_style)
status_label.pack(padx=10, pady=10)

# Enable drag-and-drop functionality
root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', lambda e: handle_dropped_file(e.data))

# Run the GUI event loop
root.mainloop()