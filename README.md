# My Digital Twin

A conversational, AI-powered professional profile built with Gradio and the OpenAI API. The app retrieves answers from a local RAG knowledge base built from the `knowledge/` folder, then answers visitors' questions in character.

**Live app:** [my-digital-twin-37yz.onrender.com](https://my-digital-twin-37yz.onrender.com/)

## Requirements

- Python 3.12 or later
- [uv](https://docs.astral.sh/uv/)
- An OpenAI API key

## Setup

Clone the repository and create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_api_key_here
```

Add your profile content as `.md`/`.txt` files in the `knowledge/` folder, then build the search index:

```bash
uv run rag.py
```

This creates a local index in `data/` (`rag_index.npy` + `rag_index.json`). Rebuild it whenever you edit the knowledge files.

Install the locked dependencies and start the app:

```bash
uv run app.py
```

uv automatically creates the virtual environment and installs the dependencies declared in `pyproject.toml`. The Gradio interface opens in your browser.

## Deploying to Render

Create a new **Web Service** from this repository and configure it as follows:

| Setting | Value |
| --- | --- |
| Build Command | `uv sync --frozen && uv cache prune --ci` |
| Start Command | `uv run app.py` |

In Render's **Environment** settings, add:

```env
OPENAI_API_KEY=your_api_key_here
```

Before deploying, make sure the Gradio app listens on Render's host and assigned port:

```python
import os

# ...
.launch(
    css=CSS,
    js=JS,
    theme=gr.themes.Base(),
    server_name="0.0.0.0",
    server_port=int(os.environ.get("PORT", 10000)),
)
```

## How it works

`context.py` loads the profile documents and builds the system prompt. `app.py` sends each chat message to the OpenAI API using `gpt-5.4-mini`. When a visitor provides an email address, or the twin cannot answer a question, `tools.py` sends a follow-up notification through Pushover.

## Privacy

Do not commit `.env`. It can contain API credentials and notification tokens. Configure these values as environment variables in Render instead.
