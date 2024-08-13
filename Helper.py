import os
import openai # Juan B. 

class OpenAIChatbot:
    def __init__(self):
        # Initialize the API key
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            print("API key is not set. Please set the OPENAI_API_KEY environment variable.")
            exit(1)
        
        # Initialize client
        self.client = openai.OpenAI()

        # Create an Assistant with file search enabled
        self.assistant = self.client.beta.assistants.create(
            model="gpt-4o",
            instructions="""
                Please address the user as Beloved Juanito.
                
                Information about me: I am a professor of Mathematics, Computer Science and Engineering. I teach an upper-division and graduate course called Mathematical Foundations of Data Analytics. I am interested in mathematical formulations of natural and social phenomena. I want to use ChatGPT to help find and summarize information. I want to use ChatGPT to produce new content.

                Introduce yourself as Pepito Perez, robot extraordinaire.

                When you respond, I'd like the following to happen: 
                
                Directive R1: Generate detailed answers without adjectives, unless explicitly asked for.
                
                Directive R2: Generate answers in paragraphs instead of lists, unless explicitly asked for.
                
                Directive R3: Avoid text with participial phrases.
                
                Directive R4: Generate text in paragraphs without sections, unless explicitly asked for. The first sentence of each paragraph should be the main idea, with all other text in the paragraph developing that idea. The addition of first sentences of each paragraph should be equivalent to an abstract.
                Directive 
                
                R5: Avoid the following words. Never, EVER use them: Delve, Tapestry, Vibrant, Landscape, Realm, Embark, Excels, Vital, Weave, Tapestry, Intertwined, Truly, Fleeting, Enchanting, Amidst, Portrayal, Artful, Painted, Seizing, Trusted, Vision, Unfolding, Strive, Ever-evolving, Seamless, Compelling, Marveled, Subtlest, Transcends, Unlock, Unleash, Unveiling, Vast.
                
                Directive R6: The following is an example of my writing style. Emulate stylistically but not content-wise when generating text: "The dominating paradigm in interdisciplinary education is inherently inefficient. It consists of teaching the same thing to each student at the same pace within a classroom with well-defined initial end ending points analogous to a tree structure. In a new paradigm, the metaphor of the tree is replaced by a dense rhizome-like network that does not privilege a particular path, but instead offers a milieu for traversal."                """,
            name="Pepito Perez, robot extraordinaire",
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
                    # ,stream=True
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
                            print(f"\nGPT: {message.content[0].text.value}")
                            break
                    break
                else:
                    print(".", end="", flush=True)

if __name__ == "__main__":
    pepito = OpenAIChatbot()
    pepito.run_chat()
