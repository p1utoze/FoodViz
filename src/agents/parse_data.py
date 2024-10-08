import os
import re

import faiss
import pandas as pd
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.schema import Document, MetadataMode
from llama_index.embeddings.voyageai import VoyageEmbedding
from llama_index.vector_stores.faiss import FaissVectorStore

from src.utils.config import PROJECT_ROOT

load_dotenv()

d = 1536
faiss_index = faiss.IndexFlatL2(d)

# Load the VoyageEmbedding model
embed_model = VoyageEmbedding(model_name="voyage-large-2", voyage_api_key=os.environ["VOYAGE_API_KEY"])


# Load and preprocess the data
def preprocess_and_vectorize_data(file_path, data_store_path=None):
    df = process_data(file_path)

    # Combine all information into a single string for each item
    # print(df.head())

    # Create documents for LlamaIndex
    documents = []
    for _, row in df.iterrows():
        document = Document(
            text=row['local_name'],
            metadata={"name": row['name'], "scientific_name": row['scie'], "tags": row['tags'], "lang": row['full_lang_name']},
            metadata_seperator="::",
            metadata_template="{key}=>{value}",
            text_template="Metadata: {metadata_str}\n-----\nContent: {content}",
        )
        documents.append(document)

    print(documents[5], documents[5].metadata, documents[5].get_content(metadata_mode=MetadataMode.EMBED), sep='\n')

    vector_store = FaissVectorStore(faiss_index=faiss_index)
    # create storage context using default stores
    storage_context = StorageContext.from_defaults(
        vector_store=vector_store,
    )
    storage_context.persist(data_store_path)

    # Create nodes from documents
    parser = SimpleNodeParser.from_defaults(separator=";")  # Default separator is "\n"
    nodes = parser.get_nodes_from_documents(documents)
    index = VectorStoreIndex(embed_model=embed_model, nodes=nodes, storage_context=storage_context, show_progress=True)
    index.storage_context.persist(data_store_path)
    return index




def process_data(file_path):
    df = pd.read_csv(file_path)
    langs = pd.read_csv(PROJECT_ROOT / "data" / "languages.csv")
    df["lang_names"] = df["lang"].apply(lambda x: str(x).split("; "))
    df = df.explode("lang_names").reset_index(drop=True)
    df["lang_names"] = df["lang_names"].apply(lambda x: x.strip())
    df["lang_names"] = df["lang_names"].astype(str)
    df["lang"] = df["lang"].astype(str)
    df["abbr"] = df["lang_names"].apply(lambda x: re.split(r"(?<=\.)\s", x)[0])
    df["local_name"] = df["lang_names"].str.extract(r"\. (.*)")
    df2 = pd.merge(df, langs, left_on="abbr", right_on="abbr", how="left")
    df2 = df2.rename(columns={"lang_y": "full_lang_name"})
    df2.drop(columns=["abbr", "id"], inplace=True)
    # print(df2[["name", "local_name", "full_lang_name"]].head(15))
    return df2

if __name__ == "__main__":
    # process_data(PROJECT_ROOT / "data" / "food_local_langs.csv")
    data_path = "../data/context_storage"
    # index = preprocess_and_vectorize_data(file_path=PROJECT_ROOT / "data" / "food_local_langs.csv", data_store_path=data_path)
    index = load_retriever(data_path)
    retriever = index.as_retriever(similarity_top_k=5)
    nodes = retriever.retrieve("dunglina dakadi")
    for node in nodes:
        print(node.text, node.metadata, node.score)


