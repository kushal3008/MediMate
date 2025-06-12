from langchain_pinecone import PineconeVectorStore
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
import os
from dotenv import load_dotenv
from src.helper import load_pdf,text_split,download_hugging_face_embeddings

load_dotenv()

PINECONE_API_KEY=os.environ.get('PINECONE_API_KEY')
Ollama_API_KEY=os.environ.get('Ollama_API_KEY')

import os
os.environ["PINECONE_API_KEY"]="pcsk_2CMN9z_QQWYTdsd89TEGCU19dNRKUFA7D7Pqc5CtTfqqQMESw6otxhDG8vGKGa1UboCech"
os.environ["Ollama_API_KEY"]="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"


extracted_data=load_pdf(data='C:/Users/Nisarg/OneDrive/Desktop/7 Project/Medical-Chatbot/Data/')

text_chunks=text_split(extracted_data)
embeddings=download_hugging_face_embeddings()

pc = Pinecone(api_key="pcsk_2CMN9z_QQWYTdsd89TEGCU19dNRKUFA7D7Pqc5CtTfqqQMESw6otxhDG8vGKGa1UboCech")
index_name ="askmedi"
pc.create_index(
    name=index_name,
    dimension=384,
    metric="cosine",
    spec=ServerlessSpec(
        cloud="aws",
        region="us-east-1"
        
    )
)
docsearch=PineconeVectorStore.from_documents(
    documents=text_chunks,
    index_name=index_name,
    embedding=embeddings,
)