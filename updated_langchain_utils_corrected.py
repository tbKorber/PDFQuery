# langchain_utils.py

from urllib.parse import urlparse
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

sbert_model = SentenceTransformer('paraphrase-distilroberta-base-v1')


from sentence_transformers import SentenceTransformer

class SBERT_Encoder:
    def __init__(self, model_name='paraphrase-distilroberta-base-v1'):
        self.model = SentenceTransformer(model_name)
    
    def encode_queries(self, queries):
        return self.model.encode(queries, convert_to_tensor=True)


def queryPDF(openaikey, embeddings, index, query):
    try:
        llm = ChatOpenAI(temperature=0.2, openai_api_key=openaikey, verbose=True)
        system_message = SystemMessage(content="You are a PDF Search Engine. You answer queries with revelant info from the provided PDF from a Pinecone index already chosen.")
        print(f"emb: {embeddings}\nidx: {index}")
        sbert_encoder = lambda text: sbert_model.encode([text], convert_to_tensor=True)
        retriever = PineconeHybridSearchRetriever(index=index, embeddings=embeddings, sparse_encoder=sbert_encoder)
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
    except Exception as e:
        error = f"{e}"
        print(error)
        return error

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