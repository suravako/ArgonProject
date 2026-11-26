from google import genai

client = genai.Client()
response = client.models.generate_content(model="gemini-4-argon", contents="Say hello")
print(response.text)
