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




class TrackingOpenAIChatCompletionClient(OpenAIChatCompletionClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.call_count = 0

    async def acompletion(self, *args, **kwargs):
        self.call_count += 1
        return await super().acompletion(*args, **kwargs)
    

async def main():
    model_client = TrackingOpenAIChatCompletionClient(
        model="deepseek/DeepSeek-R1-0528",
        base_url="https://models.github.ai/inference",
        api_key=token,
        model_info={
            "vision": False,
            "function_calling": False,
            "json_output": False,
            "family": ModelFamily.R1,
            "structured_output": True,
        },
    )

    coder = AssistantAgent(
        "coder",
        model_client=model_client,
        system_message="You are a senior engineer. Output only runnable Python code inside ```python``` blocks."
    )

    executor = CodeExecutorAgent(
        "executor",
        model_client=model_client,
        code_executor=LocalCommandLineCodeExecutor(work_dir=Path.cwd() / "runs")
    )

    user = UserProxyAgent("user")
    termination = TextMentionTermination("exit", sources=["user"])

    team = RoundRobinGroupChat([user, coder, executor], termination_condition=termination, max_turns=12)

    try:
        await Console(team.run_stream())
    finally:
        print(f"Total LLM calls: {model_client.call_count}")
        await model_client.close()

if __name__ == "__main__":
    asyncio.run(main())
