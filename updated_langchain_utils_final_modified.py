# langchain_utils.py

from urllib.parse import urlparse
import urllib.request
import requests
from pypdf import PdfReader
from io import BytesIO
from os.path import exists
from langchain import LLMChain
# from langchain.prompts import PromptTemplate
from langchain.document_loaders import (
    OnlinePDFLoader, UnstructuredPDFLoader
    )
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Pinecone
from langchain.agents import (
    initialize_agent, # tool, AgentType,
    Tool, AgentExecutor, OpenAIFunctionsAgent
    )
from langchain.retrievers import PineconeHybridSearchRetriever
from langchain.chains import (
    RetrievalQA, StuffDocumentsChain
    )
# from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage
from langchain.embeddings.openai import OpenAIEmbeddings
from sentence_transformers import SentenceTransformer
import pinecone
import json as json

# sbert_model = SentenceTransformer('paraphrase-distilroberta-base-v1')


class SBERT_Encoder:
    def __init__(self, model_name='paraphrase-distilroberta-base-v1'):
       self.model = SentenceTransformer(model_name)
    
    def encode_queries(self, queries):
        # Ensure queries is a list
        if not isinstance(queries, list):
            queries = [queries]
        encoded = self.model.encode(queries, convert_to_tensor=True)
        # Add an additional dimension
        encoded = encoded.unsqueeze(0)
        return encoded

    def encode(self, text):
        # Ensure text is a list
        if not isinstance(text, list):
            text = [text]
        encoded = self.model.encode(text, convert_to_tensor=True)
        # Add an additional dimension
        encoded = encoded.unsqueeze(0)
        return encoded

def extract_text_from_remote_pdf(url):
    # Step 1: Stream the content of the remote PDF
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Check if request was successful

    # Step 2: Use BytesIO to convert the content stream to a file-like object
    pdf_content = BytesIO(response.content)

    # Step 3: Pass the file-like object to PdfReader and extract text
    reader = PdfReader(pdf_content)
    text = ""
    for page_num in range(len(reader.pages)):
        text += reader.pages[page_num].extract_text()
    
    return text

def queryPDF(path, openaikey, embeddings, index, indexname, query):
    # try:
        with open(path, 'r') as config:
            data = json.load(config)
            pdf_urls: list = data["SETTINGS"]["INDEXES"][indexname]["urls"]
        corpus = []
        for url in pdf_urls:
            corpus.append(extract_text_from_remote_pdf(url))

        llm = ChatOpenAI(temperature=0.2, openai_api_key=openaikey, verbose=True)
        system_message = SystemMessage(content="You are a PDF Search Engine. You answer queries with revelant info from the provided PDF from a Pinecone index already chosen.")
        encoder = SentenceTransformer('paraphrase-distilroberta-base-v1')
        corpus_embeddings = encoder.encode(corpus)
        retriever = PineconeHybridSearchRetriever(index=index, embeddings=corpus_embeddings)
        prompt = OpenAIFunctionsAgent.create_prompt(system_message=system_message)
        llm_chain = LLMChain(llm=llm, prompt=prompt, verbose=True)
        combine_chain = StuffDocumentsChain(llm_chain=llm_chain, document_separator="\n\n", document_variable_name="input", verbose=True)
        retrieval_qa = RetrievalQA(retriever=retriever, combine_documents_chain=combine_chain, verbose=True)
        run_pdf_search = lambda q: run_search(query=q, retrieval=retrieval_qa)
        tool_kit = [
            Tool(name = "pdf_search", func = run_pdf_search, description = "Allows you to search the PDF within the index of Pinecone")
        ]
        agent = OpenAIFunctionsAgent(llm=llm, tools=tool_kit, retrieval_qa=retrieval_qa, prompt=prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tool_kit, verbose=True)
        response = agent_executor.run(query)
        return response
    # except Exception as e:
    #     error = f"{e}"
    #     print(error)
    #     return error

# @tool    
def run_search(query, retrieval: RetrievalQA):
    result = retrieval.run(query)
    print(result)
    return result

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

if(__name__ == '__main__'):
    print(__name__)
    with open("LangChainUI.py") as f:
        exec(f.read())