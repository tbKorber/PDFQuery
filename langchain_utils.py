# langchain_utils.py

from urllib.parse import urlparse
from os.path import exists
from langchain import LLMChain
from langchain.prompts import PromptTemplate
from langchain.document_loaders import OnlinePDFLoader, UnstructuredPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Pinecone
from langchain.agents import AgentType, initialize_agent, Tool
from langchain.retrievers import PineconeHybridSearchRetriever
from langchain.chains import RetrievalQA, StuffDocumentsChain
from langchain.llms import OpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
import pinecone
import openai

def queryPDF(openaikey, embeddings, index, query):
    try:
        llm = OpenAI(temperature=0.2, openai_api_key=openaikey)
        retriever = PineconeHybridSearchRetriever(
            index= index,
            embeddings=embeddings
        )
        prompt = PromptTemplate(template="Search the PDF for an answer to this question: {input}", input_variables=["input"])
        llm_chain = LLMChain(llm=llm, prompt=prompt)
        combine_chain = StuffDocumentsChain(llm_chain=llm_chain)
        retrieval_qa = RetrievalQA(retriever=retriever, combine_documents_chain=combine_chain)
        query_dict = {"input": query}
        run_pdf_search = lambda: run_search(query=query, retrieval=retrieval_qa)
        tool_kit = [
            Tool(
            name = "PDF Search",
            func = run_pdf_search,
            description = "Search PDF for answers"
            )
        ]
        agent = initialize_agent(
            agent = AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            tools = tool_kit,
            llm = llm,
            retrieval_qa = retrieval_qa
        )
        response = agent(query_dict)
        return response
    except Exception as e:
        error = f"{e}"
        print(error)
        return error
    
def run_search(query, retrieval):
    response = retrieval.run(query)
    print(response)
    return response

def uploadPDF(embeddings: OpenAIEmbeddings, indexname: str, pdf):
    # pdf = input("PDF Url/Path: ")
    loader = load_pdf(pdf)
    data = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=20)
    texts = text_splitter.split_documents(data)

    Pinecone.from_texts([t.page_content for t in texts], embeddings, index_name=indexname)

    return "Upload Success" if True else "Upload Failed"

def load_pdf(url):
    loader = UnstructuredPDFLoader(url) if is_local(url) else OnlinePDFLoader(url)
    return loader

def is_local(url):
    url_parsed = urlparse(url)
    if url_parsed.scheme in ('file', ''):
        return exists(url_parsed.path)
    return False

def get_all_indexes(pineconekey, pineconeenv):
    pinecone.init(
        api_key=pineconekey,
        environment=pineconeenv
    )
    index_list = pinecone.list_indexes()
    return index_list

def load_pdf(url):
    loader = UnstructuredPDFLoader(url) if is_local(url) else OnlinePDFLoader(url)
    return loader

def is_local(url):
    url_parsed = urlparse(url)
    if url_parsed.scheme in ('file', ''):
        return exists(url_parsed.path)
    return False