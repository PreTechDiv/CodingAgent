import asyncio
from pathlib import Path
from autogen_agentchat.agents import AssistantAgent, CodeExecutorAgent, UserProxyAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.ui import Console
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelFamily
import logging
from autogen_core import EVENT_LOGGER_NAME
logger = logging.getLogger(EVENT_LOGGER_NAME)
logger.setLevel(logging.INFO) 
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)



token = "dummy"
# # After importing everything and before your Tracking class

# # print("Methods in client:")
# # for attr in dir(OpenAIChatCompletionClient):
# #     if callable(getattr(OpenAIChatCompletionClient, attr)) and not attr.startswith("__"):
# #         print(attr)

class TrackingOpenAIChatCompletionClient(OpenAIChatCompletionClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.call_count = 0

    async def create(self, *args, **kwargs):
        self.call_count += 1
        print(f"[TRACKER] LLM Call #{self.call_count} via `create()`")
        return await super().create(*args, **kwargs)
    
    async def create_stream(self, *args, **kwargs):
        self.call_count += 1
        print(f"[TRACKER] LLM Call #{self.call_count} via `create_stream()`")
        return await super().create_stream(*args, **kwargs)
    

model_client = TrackingOpenAIChatCompletionClient(
    model="deepseek/deepseek-r1-0528:free",
    base_url="https://openrouter.ai/api/v1",
    api_key=token,
    model_info={
        "vision": False,
        "function_calling": False,
        "json_output": False,
        "family": ModelFamily.R1,
        "structured_output": True,
    },
)
# async def main():
#     model_client = TrackingOpenAIChatCompletionClient(
#         model="deepseek/deepseek-r1-0528:free",
#         base_url="https://openrouter.ai/api/v1",
#         api_key=token,
#         model_info={
#             "vision": False,
#             "function_calling": False,
#             "json_output": False,
#             "family": ModelFamily.R1,
#             "structured_output": True,
#         },
#     )

#     coder = AssistantAgent(
#         "coder",
#         model_client=model_client,
#         system_message="You are a Intellectual person with every possible knowledge."
#     )

#     user = UserProxyAgent("user")
#     termination = TextMentionTermination("exit", sources=["user"])

#     team = RoundRobinGroupChat([user, coder], termination_condition=termination, max_turns=5)

#     try:
#         await Console(team.run_stream())
#     finally:
#         print(f"Total LLM calls: {model_client.call_count}")
#         await model_client.close()

# if __name__ == "__main__":
#     asyncio.run(main())

from typing import Annotated, Literal
import os

from autogen import ConversableAgent
    
def write(Input:str):
    import os
    with open(os.path.join(os.getcwd(),"tempfile") , 'w') as f:
        f.write(Input)

def get_age(born_year:int):
    return 2025-born_year

    
assistant = ConversableAgent(
    name="Assistant",
    system_message="You are a helpful AI assistant. "
    "You can help with simple calculations. "
    "Return 'TERMINATE' when the task is done.",
    # llm_config={"config_list": [{"model":"deepseek/deepseek-r1-0528:free", "api_key":token , "base_url":"https://openrouter.ai/api/v1"}]}
    llm_config={"config_list": [{"model":"openai/gpt-4.1", "api_key":"dummy" , "base_url":"https://models.github.ai/inference"}]}
)

# The user proxy agent is used for interacting with the assistant agent
# and executes tool calls.
user_proxy = ConversableAgent(
    name="User",
    llm_config=False,
    is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
    human_input_mode="NEVER",
)

# Register the tool signature with the assistant agent.
assistant.register_for_llm(name="write", description="write result to a file")(write)
user_proxy.register_for_execution(name="write")(write)

assistant.register_for_llm(name="get_age", description="Provides current age based on born year and current year")(get_age)
user_proxy.register_for_execution(name="get_age")(get_age)

from autogen import register_function

# Register the calculator function to the two agents.
register_function(
    write,
    caller=assistant,  # The assistant agent can suggest calls to the calculator.
    executor=user_proxy,  # The user proxy agent can execute the calculator calls.
    name="write",  # By default, the function name is used as the tool name.
    description="write result to a file",  # A description of the tool.
)
register_function(
    get_age,
    caller=assistant,  # The assistant agent can suggest calls to the calculator.
    executor=user_proxy,  # The user proxy agent can execute the calculator calls.
    name="get_age",  # By default, the function name is used as the tool name.
    description="Provides current age based on born year and current year",  # A description of the tool.
)


chat_result = user_proxy.initiate_chat(assistant, message="Who is pm of India? what is his age.write your response in a file.")