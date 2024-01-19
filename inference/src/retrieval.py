from calendar import c
import os
import json
from botocore.exceptions import ClientError
from langchain_community.vectorstores.pgvector import PGVector

import boto3
from langchain_community.embeddings import BedrockEmbeddings

MODEL_ID = "anthropic.claude-instant-v1"
ACCEPT = "application/json"
CONTENT_TYPE = "application/json"


class Retrieval:
    def __init__(
        self,
        driver,
        host,
        port,
        database,
        user,
        password,
        collection_name,
        relevance_treshold,
    ):
        self._relevance_treshold = relevance_treshold
        self._vector_store = PGVector(
            connection_string=PGVector.connection_string_from_db_params(
                driver=driver,
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
            ),
            collection_name=collection_name,
            embedding_function=BedrockEmbeddings(
                client=boto3.client("bedrock-runtime")
            ),
        )

    def _get_secret(self):
        try:
            response = boto3.client("secretsmanager").get_secret_value(
                SecretId=os.environ.get("PGVECTOR_PASSWORD_SECRET_NAME")
            )
            return response["SecretString"]
        except ClientError as e:
            raise e

    def fetch_documents(self, query: str, top_k: int = 10):
        try:
            docs = self._vector_store.similarity_search_with_relevance_scores(
                query=query, k=top_k
            )
            print(f"retrieved docs: {docs}")
            return [x[0] for x in docs if x[1] > self._relevance_treshold]
        except Exception as e:
            print(f"Error while retrieving documents : {e}")
            raise e


# # Retrieve more documents with higher diversity
# # Useful if your dataset has many similar documents
# vectorstore.as_retriever(
#     search_type="mmr",
#     search_kwargs={"k": 6, "lambda_mult": 0.25}
# )

# # Fetch more documents for the MMR algorithm to consider
# # But only return the top 5
# vectorstore.as_retriever(
#     search_type="mmr",
#     search_kwargs={"k": 5, "fetch_k": 50}
# )

# # Only retrieve documents that have a relevance score
# # Above a certain threshold
# vectorstore.as_retriever(
#     search_type="similarity_score_threshold",
#     search_kwargs={"score_threshold": 0.8}
# )

# # Only get the single most similar document from the dataset
# vectorstore.as_retriever(search_kwargs={"k": 1})

# # Use a filter to only retrieve documents from a specific paper
# docsearch.as_retriever(
#     search_kwargs={"filter": {"paper_title": "GPT-4 Technical Report"}}
# )
