import os
from typing import List, Dict
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, ServiceContext
from llama_index.core.llms import HuggingFaceLLM
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.agent import ReActAgent
from llama_index.core.callbacks import CallbackManager, LlamaDebugHandler
from duckduckgo_search import DDGS
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch

# Initialize LlamaIndex
llama_debug = LlamaDebugHandler(print_trace_on_end=True)
callback_manager = CallbackManager([llama_debug])

# Load Hugging Face model with 4-bit quantization
model_name = "meta-llama/Llama-2-7b-chat-hf"  # You can change this to any compatible model
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16
)

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto",
)

# Create HuggingFaceLLM
llm = HuggingFaceLLM(
    context_window=4096,
    max_new_tokens=256,
    generate_kwargs={"temperature": 0.7, "do_sample": False},
    tokenizer=tokenizer,
    model=model,
)

# Set up service context
service_context = ServiceContext.from_defaults(llm=llm, callback_manager=callback_manager)

# Load documents and create index
documents = SimpleDirectoryReader("path/to/your/documents").load_data()
index = VectorStoreIndex.from_documents(documents, service_context=service_context)

# Create query engine
query_engine = index.as_query_engine()


# DuckDuckGo search tool
def web_search(query: str) -> List[Dict[str, str]]:
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=3))
    return results


# Custom tool for web search
class WebSearchTool:
    def __init__(self):
        self.metadata = ToolMetadata(
            name="web_search",
            description="Useful for searching the web for current information"
        )

    def __call__(self, input_text: str) -> str:
        results = web_search(input_text)
        return str(results)


# Create tools
query_engine_tool = QueryEngineTool(
    query_engine=query_engine,
    metadata=ToolMetadata(
        name="vector_index",
        description="Useful for answering questions about the documents in the vector index"
    )
)

web_search_tool = WebSearchTool()

# Create ReAct agent
agent = ReActAgent.from_tools([query_engine_tool, web_search_tool], llm=llm, verbose=True)


def generate_response(query: str) -> str:
    # Get response from the agent
    response = agent.chat(query)

    # Extract sources from the vector index query
    vector_sources = [node.node.metadata for node in response.source_nodes]

    # Extract web search results
    web_sources = []
    for tool_use in response.tool_usage:
        if tool_use.tool_name == "web_search":
            web_sources = eval(tool_use.output)

    # Combine sources
    all_sources = vector_sources + web_sources

    # Format the response with sources
    formatted_response = f"Answer: {response.response}\n\nSources:\n"
    for idx, source in enumerate(all_sources, 1):
        if isinstance(source, dict):
            formatted_response += f"{idx}. {source.get('title', 'N/A')} - {source.get('href', 'N/A')}\n"
        else:
            formatted_response += f"{idx}. {source}\n"

    return formatted_response


# Example usage
query = "What are the latest advancements in renewable energy?"
result = generate_response(query)
print(result)