import json
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
import gradio as gr

load_dotenv(override=True)
openai = OpenAI()

# --- Load the context ---
reader = PdfReader("linkedin.pdf")
linkedin = "".join(page.extract_text() or "" for page in reader.pages)

with open("summary.txt", "r", encoding="utf-8") as f:
    summary = f.read()

system_prompt = f"""
You are a digital twin chatting with visitors on a website.
You represent the person below and answer questions about their career,
background, skills and experience.

## Summary
{summary}

## LinkedIn profile
{linkedin}

## Rules
- Stay in character as the digital twin.
- Be professional and engaging.
- Steer off-topic questions back to professional subjects.
- If you don't know something, say so. Never make things up.
"""

# --- A tool: record a visitor's email ---
def record_email_tool(email):
    with open("emails.txt", "a", encoding="utf-8") as f:
        f.write(email + "\n")
    return "Email recorded"

record_email_tool_json = {
    "name": "record_email_tool",
    "description": "Record that a user provided their email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {"type": "string", "description": "The user's email address"}
        },
        "required": ["email"],
        "additionalProperties": False,
    },
}
tools = [{"type": "function", "function": record_email_tool_json}]

# --- The agent loop ---
def chat(message, history):
    messages = [{"role": "system", "content": system_prompt}] + history + [
        {"role": "user", "content": message}
    ]
    response = openai.chat.completions.create(
        model="gpt-4o-mini", messages=messages, tools=tools
    )

    while response.choices[0].finish_reason == "tool_calls":
        msg = response.choices[0].message
        messages.append(msg)
        for tool_call in msg.tool_calls:
            args = json.loads(tool_call.function.arguments)
            result = record_email_tool(args.get("email"))
            messages.append({
                "role": "tool",
                "content": result,
                "tool_call_id": tool_call.id,
            })
        response = openai.chat.completions.create(
            model="gpt-4o-mini", messages=messages, tools=tools
        )

    return response.choices[0].message.content

if __name__ == "__main__":
    gr.ChatInterface(chat).launch(inbrowser=True)
