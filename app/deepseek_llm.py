import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

endpoint = "https://models.github.ai/inference"
model = "deepseek/DeepSeek-R1-0528"
token = os.environ["GITHUB_TOKEN"]

def get_deepseek_llm_client():
    client = ChatCompletionsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(token),
    )

    return client

def get_deepseek_response(client):
    response = client.complete(
        messages=[
            UserMessage("What is the capital of France?"),
        ],
        max_tokens=1000,
        model=model
    )

    print(response.choices[0].message.content)

