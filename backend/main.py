import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from openai import OpenAI 
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)

class ChatRequest(BaseModel):
    user_id: str
    query: str
    role: str
    course: str
    level: str

@app.get("/")
def home():
    return {"status": "Student AI Backend Online"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), user_id: str = Form(...)):
    # 1. Read File (Simulated text extraction for demo)
    # For production: use PyPDF2 for PDFs or Whisper for Audio here
    content = (await file.read()).decode("utf-8", errors="ignore")

    # 2. Create Embedding
    response = client.embeddings.create(input=content[:8000], model="text-embedding-3-small")
    embedding = response.data[0].embedding

    # 3. Save to Supabase
    data = {
        "user_id": user_id,
        "content": content,
        "metadata": {"filename": file.filename},
        "embedding": embedding
    }
    supabase.table("documents").insert(data).execute()
    
    return {"message": "File processed successfully"}

@app.post("/chat")
async def chat(req: ChatRequest):
    # 1. Embed Query
    query_emb = client.embeddings.create(input=req.query, model="text-embedding-3-small").data[0].embedding

    # 2. Search Vector DB (RAG)
    # We use the RPC function we created in SQL
    result = supabase.rpc("match_documents", {
        "query_embedding": query_emb,
        "match_threshold": 0.5,
        "match_count": 3
    }).execute()

    # 3. Construct Context
    context_text = "\n\n".join([doc['content'] for doc in result.data])
    
    # 4. System Prompt
    if req.role == 'teacher':
        sys_prompt = f"You are a Teaching Assistant for {req.course} ({req.level}). Use the context to create lesson plans."
    else:
        sys_prompt = f"You are a Tutor for a student studying {req.course} ({req.level}). Explain simply."

    # 5. Generate Answer
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "system", "content": f"Reference Materials:\n{context_text}"},
            {"role": "user", "content": req.query}
        ]
    )

    return {"answer": completion.choices[0].message.content}