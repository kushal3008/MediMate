from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader


#Extract data 
def load_pdf(data):
    loader=DirectoryLoader(data,
                            glob="*.pdf",
                            loader_cls=PyPDFLoader)
    documents=loader.load()

    return documents


#split Data 
def text_split(extracted_data):
    text_splitter=RecursiveCharacterTextSplitter(chunk_size=500,chunk_overlap=20)
    text_chunks=text_splitter.split_documents(extracted_data)
    return text_chunks


#Download Embedding from hgging face
def download_hugging_face_embeddings():
    embeddings=HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
    return embeddings