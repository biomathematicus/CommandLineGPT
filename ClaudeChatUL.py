import anthropic
import os
import base64
import mimetypes

# Set up the API client
apiKey = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=apiKey)

# Function to encode file to base64
def encode_file(file_path):
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read()).decode('utf-8')

# Function to get MIME type
def get_mime_type(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or 'application/octet-stream'

# Start the chat loop
messages = []

while True:
    # Get user input
    user_input = input("You: ")
    
    # Check if the user wants to exit
    if user_input.lower() in ['exit', 'quit', 'bye']:
        print("Claude: Goodbye!")
        break
    
    # Check if the user wants to upload a file
    if user_input.lower().startswith('upload:'):
        file_path = user_input.split(':', 1)[1].strip()
        try:
            file_name = os.path.basename(file_path)
            file_content = encode_file(file_path)
            mime_type = get_mime_type(file_path)
            
            # Check if it's an image file
            if mime_type.startswith('image/'):
                user_message = {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": file_content
                            }
                        },
                        {
                            "type": "text",
                            "text": f"I've uploaded an image file named {file_name}. Please analyze it."
                        }
                    ]
                }
            else:
                # For non-image files, just mention the upload without including the file
                user_message = {
                    "role": "user",
                    "content": f"I've uploaded a file named {file_name} of type {mime_type}. However, I can't include non-image files in this conversation."
                }
            
            messages.append(user_message)
            print(f"File '{file_name}' processed successfully.")
        except Exception as e:
            print(f"Error processing file: {e}")
            continue
    else:
        # Add user message to the conversation
        messages.append({"role": "user", "content": user_input})
    
    # Send the message to Claude and get the response
    try:
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0.99,
            messages=messages
        )
        
        # Print Claude's response
        assistant_message = response.content[0].text
        print("Claude:", assistant_message)
        
        # Add Claude's response to the conversation
        messages.append({"role": "assistant", "content": assistant_message})
    except anthropic.BadRequestError as e:
        print(f"Error: {e}")
        # Remove the last user message if there was an error
        if messages and messages[-1]["role"] == "user":
            messages.pop()