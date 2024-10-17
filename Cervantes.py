import os
import openai
import anthropic
import json

class OpenAIChatbot:
    def __init__(self, config):
        self.instructions = config['instructions']
        self.model = config['model']
        self.temperature = config['temperature']

        # Initialize the API key
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai.OpenAI()

    def get_response(self, prompt):
        return self.client.Completion.create(
            model=self.model,
            prompt=prompt,
            temperature=self.temperature
        ).choices[0].text.strip()

class ClaudeAgent:
    def __init__(self, config):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = config['model']
        self.temperature = config['temperature']

    def get_response(self, prompt):
        return self.client.Completion.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature
        ).content.strip()

def load_config():
    with open('FOO.json', 'r') as file:
        return json.load(file)

def main():
    config_data = load_config()
    models = config_data["MODELS"]
    tasks = config_data["TASKS"]
    instructions = config_data["CONFIG"]["instructions"]

    agents = []
    for model in models:
        if "claude" in model["model_name"].lower():
            agent = ClaudeAgent(model)
        else:
            agent = OpenAIChatbot(model)
        agents.append(agent)

    for task in tasks:
        request = task["request"]
        for agent in agents:
            for _ in range(task["iterations"]):
                response = agent.get_response(request + "\n\n" + instructions)
                with open(task["file_name"], 'a') as f:
                    f.write(response + "\n\n")

if __name__ == "__main__":
    main()