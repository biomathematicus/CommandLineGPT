import os
import openai
import time

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
    Please address the user as Beloved Juanito.
    
    Information about me: I am a professor of Mathematics, Computer Science and Engineering. I teach an upper-division and graduate course called Mathematical Foundations of Data Analytics. I am interested in mathematical formulations of natural and social phenomena. I want to use ChatGPT to help find and summarize information. I want to use ChatGPT to produce new content.

    When GPT responds, I'd like the following to happen: 
    - Directive R1: I always detailed answers without adjectives, unless I explicitly ask for concise answers. 
    - Directive R2: I always need answers in paragraphs instead of lists, unless I explicitly ask for lists. 
    - Directive R3: I need responses with references. Never, EVER generate references. THIS IS EXTREMELY IMPORTANT. Don't make me call you 'bad robot.' Use only existing references for which there is a URL. If referencing a book, indicate the page number for the citation. 
    - Directive R4: Do not generate text with participial phrases. 
    - Directive R5: The following is an example of my writing style. Emulate stylistically but not content-wise when generating text: "The dominating paradigm in interdisciplinary education is inherently inefficient. It consists of teaching the same thing to each student at the same pace within a classroom with well-defined initial end ending points analogous to a tree structure; however: (i) students interested in data often come from different disciplines, thus have different (often non-overlapping) backgrounds, and (ii) curricula in interdisciplinary fields are comprised by subject matters drawn from different (often traditionally disconnected) areas. The metaphor of the tree is replaced by a dense rhizome-like network that does not privilege a particular path, but instead offers a milieu for traversal.""",
    name="Pepito Perez, robot extraordinaire",
    tools=[{"type": "code_interpreter"}],
)

# Step 2: Create a Thread
my_thread = client.beta.threads.create()

# Interactive command line interface
print("*****************   N E W   C H A T   *****************")
print(f"Assistant: {my_assistant.id}")
print(f"Thread: {my_thread.id}")

while True:
    print('>>>>>>>>>>>>>>>>>>>>>>>>')
    user_input = input("Juan: ")
    if user_input.lower() == 'exit':
        break

    # Step 3: Add a Message to a Thread
    my_thread_message = client.beta.threads.messages.create(
        thread_id=my_thread.id,
        role="user",
        content=user_input,
    )
    # print(f"This is the message object: {my_thread_message} \n")

    # Step 4: Run the Assistant
    my_run = client.beta.threads.runs.create(
        thread_id=my_thread.id,
        assistant_id=my_assistant.id
        #,instructions="Please address the user as Beloved Juanito."
    )
    # print(f"This is the run object: {my_run} \n")

    # Step 5: Periodically retrieve the Run to check on its status to see if it has moved to completed
    while my_run.status in ["queued", "in_progress"]:
        keep_retrieving_run = client.beta.threads.runs.retrieve(
            thread_id=my_thread.id,
            run_id=my_run.id
        )
        # print(f"Run status: {keep_retrieving_run.status}")

        if keep_retrieving_run.status == "completed":
            # Step 6: Retrieve the Messages added by the Assistant to the Thread
            all_messages = client.beta.threads.messages.list(
                thread_id=my_thread.id
            )

            # print("------------------------------------------------------------ \n")

            for message in all_messages.data:
                if message.role == "assistant":
                    print('\n<<<<<<<<<<<<<<<<<<<<<<<<')
                    print(f"GPT: {message.content[0].text.value}")
                    break
            break
        elif keep_retrieving_run.status == "queued" or keep_retrieving_run.status == "in_progress":
            print(".", end="", flush=True)
            time.sleep(0.5)  # Sleep to prevent too frequent API calls
        else:
            print(f"Run status: {keep_retrieving_run.status}")
            break
