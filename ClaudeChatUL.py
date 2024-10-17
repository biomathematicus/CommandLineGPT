import anthropic
import os
import PyPDF2

# Set up the API client
apiKey = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=apiKey)

def extract_text_from_pdf(file_path):
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    return text

def upload_file(file_path):
    """Simulate file upload for Anthropic (you can modify based on actual API needs)."""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None
    try:
        print(f"File uploaded successfully: {file_path}")
        return file_path  # Simulate successful file upload
    except Exception as e:
        print(f"Failed to upload file: {e}")
        return None

# Start the chat loop
messages = []

print("*****************   N E W   C H A T   *****************")

while True:
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>")
    user_input = input("Juan: ")

    # Check if the user wants to exit
    if user_input.lower() in ['exit', 'quit', 'bye']:
        print("Claude: Goodbye!")
        break
    
    # Handle file upload with the "file:" prefix
    if user_input.startswith("file:"):
        file_path = user_input[5:].strip()
        file_id = upload_file(file_path)
        if file_id:
            file_content = extract_text_from_pdf(file_id)
            user_message = f"I've uploaded a PDF file. Here's the content:\n\n{file_content}\n\nPlease analyze this PDF content."
            messages.append({"role": "user", "content": user_message})
            print(f"File '{file_path}' uploaded and processed successfully.")
            print(">>>>>>>>>>>>>>>>>>>>>>>>>>")
            continue

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
        assistant_message = response.content[0].text
    except Exception as e:
        assistant_message = f"Error: {e}"

    # Print Claude's response with <<<<<< markers
    print("\n<<<<<<<<<<<<<<<<<<<<<<<<<<")
    print(f"Claude: {assistant_message}")
    
    # Add Claude's response to the conversation
    messages.append({"role": "assistant", "content": assistant_message})
