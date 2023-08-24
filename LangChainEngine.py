from urllib.parse import urlparse
from os.path import exists
from langchain.document_loaders import OnlinePDFLoader, UnstructuredPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Pinecone
from langchain.llms import OpenAI
from langchain.chains.question_answering import load_qa_chain
import openai
from LangChainUI import get_lcui_instance, OpenAIEmbeddings, pinecone

lcui_instance = get_lcui_instance()

def main():
    embeddings, index = lcui_instance.initialize_pinecone()
    
    choice = input("Read or Write?: ")
    match choice:
        case "Read" | "read" | "r" | "R":  
            queryPDF(embeddings, index)

        case "Write" | "write" | "w" | "W":
            uploadPDF(embeddings)

def queryPDF(embeddings: OpenAIEmbeddings, index: pinecone.Index, query: str):
    llm = OpenAI(temperature=0, openai_api_key=lcui_instance.openaikey)
    chain = load_qa_chain(llm, chain_type="stuff")

    # if __name__ == 'main' : query = input("Query: ")
    openai.api_key = lcui_instance.openaikey
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

    Pinecone.from_texts([t.page_content for t in texts], embeddings, index_name=lcui_instance.headerindexreference.get())

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