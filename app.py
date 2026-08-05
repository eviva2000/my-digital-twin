import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
import gradio as gr
import requests


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

# For pushover

pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"

if pushover_user:
    if pushover_user.startswith("u"):
        print("Pushover user found and looks good")
    else:
        print("Pushover user found but doesn't start with u")
else:
    print("Pushover user not found")

if pushover_token:
    if pushover_token.startswith("a"):
        print("Pushover token found and looks good")
    else:
        print("Pushover token found but doesn't start with a")
else:
    print("Pushover token not found")

    
def push(message):
    print(f"Push: {message}")
    payload = {"user": pushover_user, "token": pushover_token, "message": message}
    requests.post(pushover_url, data=payload)

push("Digital twin app started")

def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording interest from {name} with email {email} and notes {notes}")
    return "OK"

def record_unknown_question(question):
    push(f"Recording {question} asked that I couldn't answer")
    return "OK"

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {"type": "string", "description": "The email address of this user"},
            "name": {"type": "string", "description": "The user's name, if they provided it"},
            "notes": {"type": "string", "description": "Any additional info about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "The question that couldn't be answered"},
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json}]

if __name__ == "__main__":
    gr.ChatInterface(chat).launch(inbrowser=True)
