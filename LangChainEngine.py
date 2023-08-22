from urllib.parse import urlparse
from os.path import exists
from langchain.document_loaders import OnlinePDFLoader, UnstructuredPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.chains.question_answering import load_qa_chain
import pinecone
import openai

SERVICE = {
    "OPENAI": {
        "key": "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"
    },
    "PINECONE": {
        "key": "675c29ad-309d-44f8-90b2-4de6f431cd8d",
        "env": "us-west4-gcp-free",
        "index": "langchain-test"
    }
}

def initialize_pinecone():
    pinecone.init(
        api_key=SERVICE["PINECONE"]["key"],
        environment=SERVICE["PINECONE"]["env"]
    )
    embeddings = OpenAIEmbeddings(openai_api_key=SERVICE["OPENAI"]["key"])
    index = pinecone.Index(index_name=SERVICE["PINECONE"]["index"])
    return embeddings, index

def main():
    embeddings, index = initialize_pinecone()
    
    choice = input("Read or Write?: ")
    match choice:
        case "Read" | "read" | "r" | "R":  
            queryPDF(embeddings, index)

        case "Write" | "write" | "w" | "W":
            uploadPDF(embeddings)

def queryPDF(embeddings, index, query):
    llm = OpenAI(temperature=0, openai_api_key=SERVICE["OPENAI"]["key"])
    chain = load_qa_chain(llm, chain_type="stuff")

    # if __name__ == 'main' : query = input("Query: ")
    openai.api_key = SERVICE["OPENAI"]["key"]
    query_response = openai.Embedding.create(
        model="text-embedding-ada-002",
        input=query
    )
    
    # Extract the vectors from the response
    query_vectors = query_response["data"][0]["embedding"]

    # Convert the list of vectors to a list of lists
    query_vectors_list = [query_vectors]
    
    results = index.query(query_vectors_list, top_k=5)
    
    # print(results)

    # documents = [result['document']['text'] for result in results]
    matched_ids = [match['id'] for match in results['matches']]

    documents = load_documents_from_ids(matched_ids)

    chain_result = chain.run(input_documents=documents, question=query)
    # print("Type of chain_result:", type(chain_result))

    # print("Chain Result:", chain_result)

    return "".join(chain_result)

def load_documents_from_ids(ids):
    # Load the documents from your data store using the given IDs
    # You should implement this logic based on how your documents are stored
    # Return a list of document objects

    # For example:
    documents = []
    for id in ids:
        document = load_document_from_id(id)
        if document:
            documents.append(document)
    return documents

def load_document_from_id(id):
    # Load a single document using the given ID
    # You should implement this logic based on how your documents are stored
    # Return a document object or None if not found

    # For example:
    # document = fetch_document_from_data_store(id)
    # return document

    return None  # Placeholder for illustration

def uploadPDF(embeddings, pdf):
    # pdf = input("PDF Url/Path: ")
    loader = load_pdf(pdf)
    data = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_documents(data)

    Pinecone.from_texts([t.page_content for t in texts], embeddings, index_name=SERVICE["PINECONE"]["index"])

    return "Upload Success" if True else "Upload Failed"

def load_pdf(url):
    loader = UnstructuredPDFLoader(url) if is_local(url) else OnlinePDFLoader(url)
    return loader

def is_local(url):
    url_parsed = urlparse(url)
    if url_parsed.scheme in ('file', ''):
        return exists(url_parsed.path)
    return False

if __name__ == "__main__": 

    main()