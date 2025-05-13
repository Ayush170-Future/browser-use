from dotenv import load_dotenv
load_dotenv()

from app.core.config import settings
from langchain_openai import ChatOpenAI
from langchain_openai import AzureChatOpenAI
from browser_use.agent.service import Agent
from browser_use.browser.browser import Browser
from browser_use.browser.browser import BrowserConfig
from browser_use.browser.context import BrowserContextConfig
from playwright._impl._api_structures import ProxySettings
from app.core.utils import clean_html,html_to_markdown
import os
import json

global_context = None
agent = None
proxy = ProxySettings(server=settings.PROXY_URL)

print("-" * 20)
print("Verifying Azure Environment Variables:")
loaded_key = os.getenv('AZURE_OPENAI_API_KEY')
loaded_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
loaded_api_version = os.getenv('OPENAI_API_VERSION')

print(f"AZURE_OPENAI_API_KEY Loaded: {'Yes' if loaded_key else 'NO'}")
print(f"AZURE_OPENAI_ENDPOINT Loaded: {'Yes' if loaded_endpoint else 'NO'}")
print(f"OPENAI_API_VERSION Loaded: {'Yes' if loaded_api_version else 'NO'}")
print("-" * 20)

if not loaded_key or not loaded_endpoint:
    raise ValueError("AZURE_OPENAI_API_KEY or AZURE_OPENAI_ENDPOINT not found in environment. Check .env file.")

llm = AzureChatOpenAI(
    azure_deployment="gpt-4o",
    temperature=0,
)

def replace_value_recursive(data, key_to_replace, new_value=""):
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            if key == key_to_replace:
                new_dict[key] = new_value
            else:
                new_dict[key] = replace_value_recursive(value, key_to_replace, new_value)
        return new_dict
    elif isinstance(data, list):
        new_list = []
        for item in data:
            new_list.append(replace_value_recursive(item, key_to_replace, new_value))
        return new_list
    else:
        return data

async def execute_task(task: str, use_global_context: bool, feature: str | None = None, planner_req: bool = False):
    global global_context, agent
    # browser_config = BrowserConfig(proxy=proxy, chrome_instance_path="chrome_instance_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    # browser = Browser()
    # browser_config = BrowserConfig()
    browser_config = BrowserConfig(proxy=proxy)
    browser = Browser(config=browser_config)

    if use_global_context and global_context:
        context = global_context
    else:
        context = await browser.new_context(
            config=BrowserContextConfig(
                trace_path="./tmp/traces/",
                # cookies_file="/Users/ayushsingh/Documents/programming/browser-use/cookies.json",
                browser_window_size={'width': 1920, 'height': 1080}
            )
        )
        if use_global_context:
            global_context = context

    agent = Agent(
        task=task,
        llm=llm,
        use_vision=False,
        browser_context=context,
        planner_llm=llm,
        max_failures=5,
        browser=browser
    )

    if not planner_req:  # Remove the planner
        agent = Agent(
            task=task,
            llm=llm,
            use_vision=False,
            browser_context=context,
            max_failures=5,
            browser=browser
        )

    await agent.run(25)

    # browser_context = agent.browser_context
    # agent_task_status=agent.task_completed
    # eval_prev_goal=agent.eval
    # memory=agent.memory
    # next_goal=agent.next_goal
    # result=agent._last_result
    # completed_functionalities=agent.completed_functionalities

    output = agent.state
    return output

async def get_current_page():
    global agent
    if agent is None:
        return {
            "success":False,
            "msg": "No agent found",
            "current_web_page": "",
            "current_markdown": ""
        }
    else:
        current_html = agent.get_current_html()
        if current_html:
            with open("current.html", "w") as f:
                f.write(current_html)

            cleaned_html = clean_html(current_html)
            markdown_content = html_to_markdown(cleaned_html)
            return {
                "success":True,
                "msg": "Agent and current HTML found",
                "current_web_page": cleaned_html,
                "current_markdown": markdown_content
            }
        else:
            return {
                "success":False,
                "msg": "Agent found but no current HTML found",
                "current_web_page": "",
                "current_markdown": ""
            }
