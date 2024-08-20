import os
import openai
import json
import tkinter as tk
from tkinter import filedialog, scrolledtext
from tkinterdnd2 import TkinterDnD, DND_FILES

class OpenAIChatbot:
    def __init__(self):
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
        self.init_gui()

    def init_gui(self):
        self.root = TkinterDnD.Tk()
        self.root.title("JuanGPT")
        self.text_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD)
        self.text_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        self.user_input = tk.Entry(self.root)
        self.user_input.pack(fill=tk.X, padx=10, pady=10)
        self.user_input.bind("<Return>", self.on_enter_pressed)
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_file_drop)
        self.root.mainloop()

    def on_enter_pressed(self, event):
        user_input = self.user_input.get().strip()
        if user_input:
            self.process_user_input(user_input)
        self.user_input.delete(0, tk.END)

    def on_file_drop(self, event):
        file_path = event.data.strip('{}')
        print(f"File dropped: {file_path}")
        self.upload_file(file_path)

    def upload_file(self, file_path):
        try:
            with open(file_path, 'rb') as file_data:
                file_object = self.client.files.create(
                    file=file_data,
                    purpose='assistants'
                )
            self.text_area.insert(tk.END, f"File uploaded successfully: ID {file_object.id}\n")
            self.text_area.see(tk.END)
            print(f"File uploaded successfully: ID {file_object.id}")
            return file_object.id
        except Exception as e:
            self.text_area.insert(tk.END, f"Failed to upload file: {e}\n")
            self.text_area.see(tk.END)
            print(f"Failed to upload file: {e}")
            return None

    def process_user_input(self, user_input):
        self.text_area.insert(tk.END, ">>>>>>>>>>>>>>>>>>>>>>>>>>\n")
        self.text_area.insert(tk.END, f"Juan: {user_input}\n")
        self.text_area.see(tk.END)

        try:
            my_thread_message = self.client.beta.threads.messages.create(
                thread_id=self.thread.id,
                role="user",
                content=user_input,
            )

            my_run = self.client.beta.threads.runs.create(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id
            )
        except Exception as e:
            self.text_area.insert(tk.END, f"Error: {e}\n")
            self.text_area.see(tk.END)
            return

        while my_run.status in ["queued", "in_progress"]:
            my_run = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread.id,
                run_id=my_run.id
            )
            if my_run.status == "completed":
                all_messages = self.client.beta.threads.messages.list(
                    thread_id=self.thread.id
                )
                for message in all_messages.data:
                    if message.role == "assistant":
                        self.text_area.insert(tk.END, "\n<<<<<<<<<<<<<<<<<<<<<<<<<<")
                        self.text_area.insert(tk.END, "\n" + self.name + f": {message.content[0].text.value}\n")
                        self.text_area.see(tk.END)
                        break
                break
            else:
                self.text_area.insert(tk.END, ".")
                self.text_area.see(tk.END)

if __name__ == "__main__":
    chatbot = OpenAIChatbot()