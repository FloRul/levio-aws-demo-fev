import json
import os
import boto3
from langchain_community.embeddings import BedrockEmbeddings
from langchain_community.vectorstores.pgvector import PGVector
from botocore.exceptions import ClientError
import time

bedrock = boto3.client("bedrock-runtime")
lambda_client = boto3.client('lambda')


def get_secret():
    secret_name = os.environ.get("PGVECTOR_PASSWORD_SECRET_NAME")
    region_name = "us-west-2"
    session = boto3.Session()
    client = session.client(
        service_name="secretsmanager",
        region_name=region_name
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        secret = get_secret_value_response["SecretString"]
        return secret
    except ClientError as e:
        print(e)
        raise (e)


PGVECTOR_DRIVER = os.environ.get("PGVECTOR_DRIVER", "psycopg2")
PGVECTOR_HOST = os.environ.get("PGVECTOR_HOST", "localhost")
PGVECTOR_PORT = int(os.environ.get("PGVECTOR_PORT", 5432))
PGVECTOR_DATABASE = os.environ.get("PGVECTOR_DATABASE", "postgres")
PGVECTOR_USER = os.environ.get("PGVECTOR_USER", "postgres")
PGVECTOR_PASSWORD = get_secret()

RELEVANCE_TRESHOLD = 0.65


def get_connection_string():
    CONNECTION_STRING = PGVector.connection_string_from_db_params(
        driver=PGVECTOR_DRIVER,
        host=PGVECTOR_HOST,
        port=PGVECTOR_PORT,
        database=PGVECTOR_DATABASE,
        user=PGVECTOR_USER,
        password=PGVECTOR_PASSWORD,
    )

    return CONNECTION_STRING


def get_vector_store(collection_name="main_collection"):
    bedrock = boto3.client('bedrock-runtime')
    return PGVector(connection_string=get_connection_string(),
                    collection_name=collection_name,
                    embedding_function=BedrockEmbeddings(client=bedrock))


def update_history(session_id, human_message, assistant_message):
    try:
        payload = {
            "session_id": session_id,
            "human_message": human_message,
            "assistant_message": assistant_message,
            "sk": time.time()
        }
        response = lambda_client.invoke(
            FunctionName=os.environ.get("MEMORY_LAMBDA_NAME"),
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        return response
    except ClientError as e:
        print(e.response['Error']['Message'])
        return e.response['Error']['Message']


def prepare_prompt(query: str, docs: list, history: list):
    final_prompt = "{}.Answer in french.\n\nAssistant:"

    basic_prompt = f"""\n\nHuman: The user sent the following message : {query}."""

    if (len(docs) > 0):
        docs_context = ".\n".join(map(lambda x: x[0].page_content, docs))
        document_prompt = f"""Use the following documents corpus to answer: <corpus>{docs_context}</corpus>."""
        basic_prompt = f"""{basic_prompt}\n{document_prompt}"""

    if (len(history) > 0):
        history_context = ".\n".join(
            map(lambda x: f"""{x['human_message']}{x['assistant_message']}""", history))
        history_prompt = f"""Consider using the following history : <history>{history_context}</history>."""
        basic_prompt = f"""{basic_prompt}\n{history_prompt}"""

    final_prompt.format(basic_prompt)
    print(final_prompt)
    return final_prompt


def prepare_lex_response(assistant_message: str, intent: str):
    return {
        "sessionState": {
            "dialogAction": {
                "type": "ElicitIntent"
            },
            "intent": {
                "name": intent,
                "state": "InProgress"
            }
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": assistant_message
            }
        ],
        "requestAttributes": {}
    }


def invoke_model(query, docs, max_tokens=512):
    prompt = prepare_prompt(query, docs)
    body = json.dumps({
        "prompt": prompt,
        "max_tokens_to_sample": max_tokens,
        "temperature": 0.3,
    })

    modelId = "anthropic.claude-instant-v1"
    accept = "application/json"
    contentType = "application/json"

    response = bedrock.invoke_model(
        body=body, modelId=modelId, accept=accept, contentType=contentType)
    body = response["body"].read().decode("utf-8")
    json_body = json.loads(body)
    return json_body['completion']


def dummy_invoke_model():
    return "this is a dummy response"


def lambda_handler(event, context):
    try:
        print(event)

        session_id = event['sessionId']
        intent = event['sessionState']['intent']['name']
        if intent == "Intent" or intent == "FallbackIntent":
            vector_store = get_vector_store(collection_name="main_collection")
            query = event['inputTranscript']

            max_tokens_to_sample = os.environ.get("MAX_TOKENS", 100)
            dev_mode = os.environ.get("DEV_MODE", 1)
            session_id = event['sessionId']

            if dev_mode == 0:
                docs = vector_store.similarity_search_with_relevance_scores(
                    query=query, k=5)

                # filter out documents with low relevance score
                # only keep the documents
                docs = [x[0] for x in docs if x[1] > RELEVANCE_TRESHOLD]

                # retrieve chat history
                history = update_history(session_id, query, docs)

                # prepare the prompt
                prompt = prepare_prompt(query, docs, history)

                response = invoke_model(query, docs, max_tokens_to_sample)
                update_history(session_id, query, response)
            else:
                response = dummy_invoke_model()

        return prepare_lex_response(response, intent)
    except Exception as e:
        print(e)
        return prepare_lex_response("Sorry, I did not understand that.")

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
