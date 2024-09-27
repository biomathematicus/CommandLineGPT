import anthropic
import os 

# Set up the API client
apiKey = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=apiKey)

# Start the chat loop
while True:
    # Get user input
    user_input = input("You: ")
    
    # Check if the user wants to exit
    if user_input.lower() in ['exit', 'quit', 'bye']:
        print("Claude: Goodbye!")
        break
    
    # Send the message to Claude and get the response
    response = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1000,
        temperature=0.7,
        messages=[
            {"role": "user", "content": user_input}
        ]
    )
    
    # Print Claude's response
    print("Claude:", response.content[0].text)