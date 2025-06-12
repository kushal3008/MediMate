from flask import Flask,render_template,jsonify,request 
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
from src.helper import load_pdf,text_split,download_hugging_face_embeddings
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM
from langchain.chains import create_retrieval_chain
from langchain_community.llms import Ollama
from src.prompt import * 
import os 
from langchain_community.embeddings import HuggingFaceEmbeddings
# or sometimes
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.chains import RetrievalQA

def load_pdf(data):
    loader=DirectoryLoader(data,
                            glob="*.pdf",
                            loader_cls=PyPDFLoader)
    documents=loader.load()

    return documents

def text_split(extracted_data):
    text_splitter=RecursiveCharacterTextSplitter(chunk_size=500,chunk_overlap=20)
    text_chunks=text_splitter.split_documents(extracted_data)
    return text_chunks


app=Flask(__name__,template_folder="templete")
load_dotenv()

PINECONE_API_KEY=os.environ.get('PINECONE_API_KEY')
Ollama_API_KEY=os.environ.get('Ollama_API_KEY')

os.environ["PINECONE_API_KEY"]="pcsk_2CMN9z_QQWYTdsd89TEGCU19dNRKUFA7D7Pqc5CtTfqqQMESw6otxhDG8vGKGa1UboCech"
os.environ["Ollama_API_KEY"]="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"

embeddings=download_hugging_face_embeddings()
embeddings = HuggingFaceEmbeddings(
    model_name='sentence-transformers/all-MiniLM-L6-v2'
)


index_name ="askmedi"

docsearch=PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings
)

retriever=docsearch.as_retriever(search_type="similarity",search_kwargs={"k":3})
from langchain_ollama import OllamaLLM
llm=Ollama(model="llama3")
# You can customize the prompt if needed


prompt=ChatPromptTemplate.from_messages(
    [
        ("system",system_prom),
        ("human","{input}"),
    ]
)

document_chain = create_stuff_documents_chain(llm,prompt)


rag_chain = create_retrieval_chain(
    retriever=retriever,
    combine_docs_chain=document_chain,
)



question_answer_chain=create_stuff_documents_chain(llm,prompt)
#rag_chain = create_retrieval_chain(combine_docs_chain=document_chain, retriever=retriever)

def bot(input):
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
    return chat_completion.choices[0].message.content

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/get",methods=["GET","POST"])
def chats():
    msg=request.args.get("msg")
    input=msg
    print(input)
    response=bot(msg)   
    return str(response)

if __name__=='__main__':
    app.run(host="0.0.0.0",port=8050,debug=True)

