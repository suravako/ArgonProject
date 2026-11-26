from google import genai

c = genai.Client()
for m in c.models.list(): print(m.name)
