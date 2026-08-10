# Knowledge base (RAG source)

Drop `.md` or `.txt` files about yourself in this folder. Everything here is
chunked, embedded, and searched by the digital twin's `search_profile` tool.

## Rebuild the index after editing

```bash
uv run rag.py
```

This regenerates the local index in `data/` (`rag_index.npy` + `rag_index.json`),
which is git-ignored and safe to delete/rebuild anytime.

## Tips

- One topic per file keeps retrieval focused (about, experience, skills, ...).
- Write in natural language; short paragraphs and bullet lists work well.
- Be specific (names, dates, numbers) — vague text retrieves poorly.
