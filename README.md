# My Digital Twin

A conversational, AI-powered professional profile built with Gradio and the OpenAI API. The app uses a LinkedIn PDF and a written summary as its source material, then answers visitors' questions in character.

## Requirements

- Python 3.12 or later
- [uv](https://docs.astral.sh/uv/)
- An OpenAI API key

## Setup

Clone the repository and create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_api_key_here
```

Make sure these source files are present in the project root:

- `linkedin.pdf` — the LinkedIn profile exported as a PDF
- `summary.txt` — a concise professional summary

Install the locked dependencies and start the app:

```bash
uv run app.py
```

uv automatically creates the virtual environment and installs the dependencies declared in `pyproject.toml`. The Gradio interface opens in your browser.

## How it works

`app.py` loads the profile documents, builds a system prompt, and sends each chat message to the OpenAI API using the `gpt-4o-mini` model. When a visitor gives an email address, the model can call a local tool that appends it to `emails.txt`.

## Privacy

Do not commit `.env` or `emails.txt`. The former contains your API credential; the latter can contain visitor personal information. Both should remain local to the deployment environment.
