import os
from dotenv import load_dotenv
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv('.env')
api_key = os.environ.get('GOOGLE_API_KEY')
genai.configure(api_key=api_key)

models = [m.name for m in genai.list_models() if 'embed' in m.name.lower()]
print("Found embedding models:", models)

for model_name in models:
    print(f"\nTesting {model_name}...")
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model=model_name, google_api_key=api_key)
        res = embeddings.embed_query("Hello")
        print(f"✅ Success! Embedding size: {len(res)}")
    except Exception as e:
        print(f"❌ Failed: {repr(e)}")
