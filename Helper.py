import os
import openai
import json

class OpenAIChatbot:
    def __init__(self, config_file="config.json"):
        # Load configuration from file
        with open(config_file, 'r') as file:
            config = json.load(file)

        self.instructions = config['instructions']
        self.model = config['model']
        self.name = config['name']

        # Initialize the API key
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            print("API key is not set. Please set the OPENAI_API_KEY environment variable.")
            exit(1)

        # Initialize client
        self.client = openai.OpenAI()

        # Create an Assistant with file search enabled
        self.assistant = self.client.beta.assistants.create(
            model=self.model,
            instructions=self.instructions,
            name=self.name,
            tools=[{"type": "file_search"}]
        )

        # Create a Thread
        self.thread = self.client.beta.threads.create()

    def upload_file(self, file_path):
        """Uploads a file to the OpenAI API."""
        try:
            with open(file_path, 'rb') as file_data:
                file_object = self.client.files.create(
                    file=file_data,
                    purpose='assistants'
                )
            print(f"File uploaded successfully: ID {file_object.id}")
            return file_object.id
        except Exception as e:
            print(f"Failed to upload file: {e}")
            return None

    def run_chat(self):
        print("*****************   N E W   C H A T   *****************")
        print(f"Assistant: {self.assistant.id}")
        print(f"Thread: {self.thread.id}")

        while True:
            print(">>>>>>>>>>>>>>>>>>>>>>>>>>")
            user_input = input("Juan: ")
            if user_input.lower() == 'exit':
                break
            
            if user_input.startswith("file:"):
                file_path = user_input[5:].strip()
                file_id = self.upload_file(file_path)
                if file_id:
                    print(f"File ID {file_id} will be used in subsequent requests")
                    # Attach the file to the thread
                    try: 
                        message = self.client.beta.threads.messages.create(
                            thread_id=self.thread.id,
                            role="user",
                            content="Query involving an uploaded file.",
                            attachments=[{"file_id": file_id, "tools": [{"type": "file_search"}]}]
                        )
                        continue
                    except Exception as e:
                        print(f"Failed to upload file: {e}")

            try:                         
                # Add a Message to a Thread
                my_thread_message = self.client.beta.threads.messages.create(
                    thread_id=self.thread.id,
                    role="user",
                    content=user_input,
                )

                # Run the Assistant
                my_run = self.client.beta.threads.runs.create(
                    thread_id=self.thread.id,
                    assistant_id=self.assistant.id
                )
            except Exception as e:
                print(f"Error: {e}")
            
            # Check the status of the run and output responses
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
                            print("\n<<<<<<<<<<<<<<<<<<<<<<<<<<")
                            print("\n" + self.name + f": {message.content[0].text.value}")
                            break
                    break
                else:
                    print(".", end="", flush=True)

if __name__ == "__main__":
    pepito = OpenAIChatbot()
    pepito.run_chat()
