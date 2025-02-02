from openai import OpenAI

client = OpenAI(
  api_key="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"
)

completion = client.chat.completions.create(
  model="gpt-4o-mini",
  store=True,
  messages=[
    {"role": "user", "content": "write a haiku about ai"}
  ]
)

print(completion.choices[0].message);
