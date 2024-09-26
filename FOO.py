import anthropic
import os
import json
import pyperclip  # This module is for copying text to the clipboard
import openai

class Anthropic:
    def __init__(self, prompt):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("API key is not set. Please set the ANTHROPIC_API_KEY environment variable.")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.prompt = prompt

    def get_response(self):
        message = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": self.prompt
                }
            ]
        )
        text_blocks = message.content
        return text_blocks[0].text if text_blocks else ""


class OpenAIChatbot:
    def __init__(self, config_file="config.json"):
        with open(config_file, 'r') as file:
            config = json.load(file)

        self.instructions = config['instructions']
        self.model = config['model']
        self.name = config['name']

        # Initialize the API key
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ValueError("API key is not set. Please set the OPENAI_API_KEY environment variable.")

        # Initialize client
        self.client = openai.OpenAI()

        self.assistant = self.client.beta.assistants.create(
            model=self.model,
            instructions=self.instructions,
            name=self.name,
            tools=[{"type": "file_search"}]
        )

        self.thread = self.client.beta.threads.create()

    def run_chat(self):
        print("*****************   N E W   C H A T   *****************")
        print(f"Assistant: {self.assistant.id}")
        print(f"Thread: {self.thread.id}")

        while True:
            user_input = input("Juan: ")
            if user_input.lower() == 'exit':
                break

            if user_input.startswith("FOO"):
                # Create an instance of the Anthropic class
                anthropic_instance = Anthropic(f"find the flaws in the following statement: {user_input[4:]}")
                response = anthropic_instance.get_response()

                # Prepend the text and copy to the clipboard
                clipboard_text = f"Anthropic found the following error in your logic. Correct: {response}"
                pyperclip.copy(clipboard_text)
                print("Text copied to clipboard!")

            else:
                # Handle the general input with OpenAI
                self.handle_openai_chat(user_input)

    def handle_openai_chat(self, user_input):
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

            while my_run.status in ["queued", "in_progress"]:
                my_run = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread.id,
                    run_id=my_run.id
                )

            if my_run.status == "completed":
                all_messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
                for message in all_messages.data:
                    if message.role == "assistant":
                        print("\n<<<<<<<<<<<<<<<<<<<<<<<<<<")
                        print("\nAssistant Response:\n", message.content[0].text.value)
                        break
            else:
                print(".", end="", flush=True)
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    chatbot = OpenAIChatbot()
    chatbot.run_chat()
