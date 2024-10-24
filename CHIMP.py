import os
import openai
import anthropic
import json
from datetime import datetime

# Create a base class that contains all properties common to all agents
class BaseAgent:
    def __init__(self, model, config):
        self.agent_name = model["agent_name"]
        self.model_code = model['model_code']
        self.model_name = model['model_name']
        self.temperature = model['temperature']
        self.general_instructions = config["general_instructions"]

# OpenAIChatbot uses the latest OpenAI API version based on Helper.py
class OpenAIChatbot(BaseAgent):
    def __init__(self, model, config):
        super().__init__(model, config)  # Initialize from BaseAgent

        # Initialize the OpenAI API key
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            print("API key is not set. Please set the OPENAI_API_KEY environment variable.")
            exit(1)

        # Initialize client and thread, assuming the assistant creation part is correct based on Helper.py
        self.client = openai.OpenAI()

        # Create an Assistant and a Thread for interactions
        self.assistant = self.client.beta.assistants.create(
            model=self.model_code,
            instructions=self.general_instructions,  
            name=self.agent_name,
            tools=[{"type": "file_search"}]
        )
        self.thread = self.client.beta.threads.create()

    def get_response(self, prompt):
        try:
            # Add a message to the thread
            self.client.beta.threads.messages.create(
                thread_id=self.thread.id,
                role="user",
                content=prompt,
            )

            # Run the Assistant to process the response
            my_run = self.client.beta.threads.runs.create(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id,
                model=self.assistant.model,  # Specify the model
                temperature=self.temperature  # Set the temperature
            )

            # Wait for the response
            while my_run.status in ["queued", "in_progress"]:
                my_run = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread.id,
                    run_id=my_run.id
                )

            # Retrieve and return the assistant's response
            if my_run.status == "completed":
                all_messages = self.client.beta.threads.messages.list(
                    thread_id=self.thread.id
                )
                for message in all_messages.data:
                    if message.role == "assistant":
                        s =  message.content[0].text.value.strip()
                        s = s.replace("```latex", "")
                        s = s.replace("```", "")
                        return s


            return "Error: Could not complete the request."
        except Exception as e:
            return f"Error: {e}"

# ClaudeAgent uses the updated syntax for Anthropic's Claude API, based on ClaudeChatUL.py
class ClaudeAgent(BaseAgent):
    def __init__(self, model, config):
        super().__init__(model, config)  # Initialize from BaseAgent
        
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.system_prompt = self.general_instructions
        self.conversation_history = []

    def get_response(self, prompt):
        try:
            # Add the user's prompt to the conversation history
            self.conversation_history.append({"role": "user", "content": prompt})

            # Send the conversation history to Claude and get the response
            response = self.client.messages.create(
                model=self.model_code,
                max_tokens=1000,
                temperature=self.temperature,
                system=self.system_prompt,
                messages=self.conversation_history
            )

            # Add Claude's response to the conversation history
            assistant_message = response.content[0].text
            self.conversation_history.append({"role": "assistant", "content": assistant_message})

            return assistant_message.strip()
        except Exception as e:
            return f"Error: {e}"
        
# Load configuration from the provided JSON file
def load_config(file_name):
    with open(file_name, 'r') as file:
        return json.load(file)

# Generate an audit trail for the log files. Added at the end of each chapter
def audit_trail(i, request, agent):
    return ("\section{Audit trail} \n\n " 
            + "\\begin{itemize}" 
            + "\n\\item \\textbf{Agent Number}: " + str(i + 1) 
            + "\n\\item \\textbf{Agent Name}: " + agent.agent_name 
            + "\n\\item \\textbf{Model Name}: " + agent.model_name 
            + "\n\\item \\textbf{Model Code}: " + agent.model_code 
            + "\n\\item \\textbf{Temperature}: " + str(agent.temperature) 
            + "\n\\item \\textbf{Date \\& Time}: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
            + "\n\\item \\textbf{Request}: " + request 
            + "\n\\end{itemize} \n\n" 
            + "%==============================  \n\n"
        )

# Main function to handle the interaction logic
def main(file_name):
    config_data = load_config(file_name)
    models = config_data["MODELS"]
    tasks = config_data["TASKS"]
    config = config_data["CONFIG"]

    # Initialize agents based on the models in the config
    agents = []
    for model in models:
        if "claude" in model["model_name"].lower():
            agent = ClaudeAgent(model, config)
        else:
            agent = OpenAIChatbot(model, config)
        agents.append(agent)

    # Initialize the harmonizer agent based on the configuration in the JSON
    harmonizer_model = {
        "agent_name": config["harmonizer_name"],
        "model_code": config["harmonizer_code"],
        "model_name": config["harmonizer_name"],
        "temperature": config["harmonizer_temperature"]
    }
    harmonizer_agent = OpenAIChatbot(harmonizer_model, config)

    # Loop through each task
    for k, task in enumerate(tasks):
        request = task["request"]
        instructions = task["instructions"]

        # Step 1: Each agent responds to the original question
        initial_responses = []
        for i, agent in enumerate(agents):
            response = agent.get_response(instructions + "\n\n" + request)
            initial_responses.append(response)
            print(f"Step 1: Each agent responds to the original question. Task {k}\n\n{audit_trail(i, 'See JSON file' , agent)}")
            with open('log_responses_' + task["file_name"], 'a') as f:
                f.write(f"{response}\n\n{audit_trail(i, request, agent)}")

        # Step 2: Each agent critiques other agents' responses individually
        critiqued_responses = [[None for _ in range(len(agents))] for _ in range(len(agents))]  # 2D array for individual critiques
        for i, agent in enumerate(agents):
            for j, other_response in enumerate(initial_responses):
                if i != j:
                    critique_prompt = f"Another LLM responded to the same question as follows. Find the flaws:\n\n{other_response}"
                    critique_response = agent.get_response(critique_prompt)
                    critiqued_responses[i][j] = critique_response  # Storing critique response for agent i critiquing agent j
                    print(f"Step 2: Each agent critiques other agents' responses individually.\nTask{k}\nReview ({i},{j})\n\n{audit_trail(i, 'See JSON file' , agent)}")
                    with open('log_critiques_' + task["file_name"], 'a') as f:
                        f.write(f"{critique_response}\n\n{audit_trail(i, request, agent)}")

        # Step 3: Each agent refines its response based on the specific critiques from others
        refined_responses = []
        for i, agent in enumerate(agents):
            critiques_for_agent = "\n\n".join([f"Criticism from another agent:\n{critiqued_responses[j][i]}" for j in range(len(agents)) if j != i])
            refine_prompt = f"Other agents criticized your response as follows. Validate criticism and refine as needed:\n\n{critiques_for_agent}"
            refined_response = agent.get_response(refine_prompt)
            refined_responses.append(refined_response)
            print(f"Step 3: Each agent refines its response based on the specific critiques from others.\nTask{k}\nReview ({i},{j})\n{audit_trail(i, 'See JSON file' , agent)}")
            with open('log_refined_' + task["file_name"], 'a') as f:
                f.write(f"{refined_response}\n\n{audit_trail(i, request, agent)}")

        # Step 4: Each agent harmonizes all refined responses into a single version of the task
        harmonized_responses = []
        for i, agent in enumerate(agents):
            combined_responses = "\n\n".join([f"Refined response from another agent:\n{resp}" for resp in refined_responses])
            harmonize_prompt = f"The following are refined responses from different agents. Harmonize these responses to produce a single unified version of the task:\n\n{combined_responses}"
            harmonized_response = agent.get_response(harmonize_prompt)
            harmonized_responses.append(harmonized_response)
            print(f"Step 4: Each agent harmonizes all refined responses into a single version of the task. \nTask{k}\n{audit_trail(i, 'See JSON file' , agent)}")
            with open('log_harmonized_' + task["file_name"], 'a') as f:
                f.write(f"{harmonized_response}\n\n{audit_trail(i, request, agent)}")

        # Step 5: The harmonizer agent creates a single output from all harmonized responses
        combined_harmonized_responses = "\n\n".join([f"Harmonized response from agent {i+1}:\n{resp}" for i, resp in enumerate(harmonized_responses)])
        final_harmonization_prompt = f"The following are harmonized responses from different agents. Produce a single unified and improved version:\n\n{combined_harmonized_responses}"
        final_response = harmonizer_agent.get_response(final_harmonization_prompt)
        print(f"Step 5: The harmonizer agent creates a single output from all harmonized responses. \nTask{k}\n{audit_trail(i, 'See JSON file' , harmonizer_agent)}")
        with open(task["file_name"], 'a') as f:
            f.write(final_response)

if __name__ == "__main__":
    main('test.json')
