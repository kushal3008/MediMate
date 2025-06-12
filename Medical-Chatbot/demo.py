from groq import Groq

client = Groq(
    api_key="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",
)
system_prom=(
    "You are an assistant for question-answering tasks"
    "Use the following pieces of retrived context to answer"
    "the question.If you don't know the answer,say thank you"
    "don't know.Use three sentence maximun and keep the"
    "answer concise."
    "\n\n"
    "{context}"
)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": system_prom,
        },
        {
            "role": "user",
            "content": f"{input}",
        }
    ],
    model="llama-3.3-70b-versatile",
    stream=False,
)

print(chat_completion.choices[0].message.content)