import ollama

r = ollama.chat(
    model="qwen2.5:7b",
    messages=[{"role": "user", "content": "In one sentence, what is a timing difference in bank reconciliation?"}],
)
print(r["message"]["content"])
