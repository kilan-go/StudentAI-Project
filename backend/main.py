import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware # <--- NEW IMPORT
from pydantic import BaseModel
from supabase import create_client, Client
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# --- FIX: ADD CORS MIDDLEWARE ---
# This allows your Streamlit app (and Mobile app) to talk to this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (change to specific URL for production)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)

class ChatRequest(BaseModel):
    user_id: str | None = None # Allow None for guests
    query: str
    role: str
    course: str
    level: str

@app.get("/")
def home():
    return {"status": "Student AI Backend Online"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), user_id: str = Form(...)):
    try:
        content = (await file.read()).decode("utf-8", errors="ignore")
        
        # Create Embedding
        response = client.embeddings.create(input=content[:8000], model="text-embedding-3-small")
        embedding = response.data[0].embedding

        # Save to Supabase
        data = {
            "user_id": user_id,
            "content": content,
            "metadata": {"filename": file.filename},
            "embedding": embedding
        }
        supabase.table("documents").insert(data).execute()
        return {"message": "File processed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        # Embed Query
        query_emb = client.embeddings.create(input=req.query, model="text-embedding-3-small").data[0].embedding

        # Search Vector DB
        result = supabase.rpc("match_documents", {
            "query_embedding": query_emb,
            "match_threshold": 0.5,
            "match_count": 3
        }).execute()

        context_text = "\n\n".join([doc['content'] for doc in result.data]) if result.data else "No context found."
        
        sys_prompt = f"You are a Tutor for {req.course} ({req.level}). Context: {context_text}"

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": req.query}
            ]
        )
        return {"answer": completion.choices[0].message.content}
    except Exception as e:
        print(f"Error: {e}")
        return {"answer": "I'm having trouble thinking right now. Please try again."}
