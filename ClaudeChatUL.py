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

# Start the chat loop
messages = []

while True:
    # Get user input
    user_input = input("You: ")
    
    # Check if the user wants to exit
    if user_input.lower() in ['exit', 'quit', 'bye']:
        print("Claude: Goodbye!")
        break
    
    # Check if the user wants to upload a PDF
    if user_input.lower().startswith('upload pdf:'):
        file_path = user_input.split(':', 1)[1].strip()
        try:
            if not file_path.lower().endswith('.pdf'):
                raise ValueError("The file must be a PDF.")
            
            file_name = os.path.basename(file_path)
            pdf_text = extract_text_from_pdf(file_path)
            
            user_message = f"I've uploaded a PDF file named '{file_name}'. Here's the content:\n\n{pdf_text}\n\nPlease analyze this PDF content."
            messages.append({"role": "user", "content": user_message})
            print(f"PDF '{file_name}' uploaded and processed successfully.")
        except Exception as e:
            print(f"Error processing PDF: {e}")
            continue
    else:
        # Add user message to the conversation
        messages.append({"role": "user", "content": user_input})
    
    # Send the message to Claude and get the response
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