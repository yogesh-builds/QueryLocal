from dotenv import load_dotenv
from google import genai

load_dotenv()                 # loads GEMINI_API_KEY from .env
client = genai.Client()       # picks up the key automatically

response = client.models.generate_content(
    model="models/gemini-3.8-flash",
    contents="Say hello to a developer starting their first AI project, in one line.",
)
print(response.text)