from ollama import Client

client = Client()

response = client.chat(
    model="llama3.1",
    messages=[
        {"role": "user", "content": "Hello Azrion, are you online?"}
    ]
)

print(response['message']['content'])