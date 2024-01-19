import json
import os
import boto3
from botocore.exceptions import ClientError
from retrieval import Retrieval
from history import History


def get_secret():
    try:
        response = boto3.client("secretsmanager").get_secret_value(
            SecretId=os.environ.get("PGVECTOR_PASSWORD_SECRET_NAME")
        )
        return response["SecretString"]
    except ClientError as e:
        raise e


PGVECTOR_DRIVER = os.environ.get("PGVECTOR_DRIVER", "psycopg2")
PGVECTOR_HOST = os.environ.get("PGVECTOR_HOST", "localhost")
PGVECTOR_PORT = int(os.environ.get("PGVECTOR_PORT", 5432))
PGVECTOR_DATABASE = os.environ.get("PGVECTOR_DATABASE", "postgres")
PGVECTOR_USER = os.environ.get("PGVECTOR_USER", "postgres")
PGVECTOR_PASSWORD = get_secret()

RELEVANCE_TRESHOLD = 0.65

MODEL_ID = "anthropic.claude-instant-v1"
ACCEPT = "application/json"
CONTENT_TYPE = "application/json"


def prepare_prompt(query: str, docs: list, history: list):
    try:
        final_prompt = (
            "{} Answer in french, do not use XML tags in your answer.\n\nAssistant:"
        )

        basic_prompt = f"""\n\nHuman: The user sent the following message : <message>{query}</message>."""

        if len(docs) > 0:
            docs_context = ".\n".join(map(lambda x: x.page_content, docs))
            document_prompt = f"""Use the following documents corpus to answer: <corpus>{docs_context}</corpus>."""
            basic_prompt = f"""{basic_prompt}\n{document_prompt}"""

        if len(history) > 0:
            history_context = ".\n".join(
                map(
                    lambda x: f"""Human:{x['HumanMessage']}\nAssistant:{x['AssistantMessage']}""",
                    history,
                )
            )
            history_prompt = f"""Consider using the following history : <history>{history_context}</history>."""
            basic_prompt = f"""{basic_prompt}\n{history_prompt}"""

        final_prompt = final_prompt.format(basic_prompt)
        return final_prompt
    except Exception as e:
        print(f"Error while preparing prompt : {e}")
        raise e


def prepare_lex_response(assistant_message: str, intent: str):
    return {
        "sessionState": {
            "dialogAction": {"type": "ElicitIntent"},
            "intent": {"name": intent, "state": "InProgress"},
        },
        "messages": [{"contentType": "PlainText", "content": assistant_message}],
        "requestAttributes": {},
    }


def invoke_model(prompt: str, max_tokens: int):
    body = json.dumps(
        {
            "prompt": prompt,
            "max_tokens_to_sample": max_tokens,
            "temperature": 0.3,
        }
    )
    try:
        response = boto3.client("bedrock-runtime").invoke_model(
            body=body, modelId=MODEL_ID, accept=ACCEPT, contentType=CONTENT_TYPE
        )
        body = response["body"].read().decode("utf-8")
        json_body = json.loads(body)
        return json_body["completion"]
    except Exception as e:
        print(f"Model invocation error : {e}")
        raise e


def lambda_handler(event, context):
    intent = event["sessionState"]["intent"]["name"]
    response = "this is a dummy response"

    enable_history = int(os.environ.get("ENABLE_HISTORY", 1))
    enable_retrieval = int(os.environ.get("ENABLE_RETRIEVAL", 1))
    max_tokens_to_sample = int(os.environ.get("MAX_TOKENS", 100))
    enable_inference = int(os.environ.get("ENABLE_INFERENCE", 1))
    top_k = int(os.environ.get("TOP_K", 10))
    embedding_collection_name = os.environ.get("EMBEDDING_COLLECTION_NAME", "docs")
    
    print(
        f"""enable_history: {enable_history}, 
          enable_retrieval: {enable_retrieval}, 
          max_tokens_to_sample: {max_tokens_to_sample}, 
          enable_inference: {enable_inference},
          top_k: {top_k},
          embedding_collection_name: {embedding_collection_name}
          """
    )

    history = History(event["sessionId"])

    try:
        if intent == "Intent" or intent == "FallbackIntent":
            query = event["inputTranscript"]
            docs = []
            chat_history = []

            if enable_inference == 1:
                if enable_retrieval == 1:
                    retrieval = Retrieval(
                        driver=PGVECTOR_DRIVER,
                        host=PGVECTOR_HOST,
                        port=PGVECTOR_PORT,
                        database=PGVECTOR_DATABASE,
                        user=PGVECTOR_USER,
                        password=PGVECTOR_PASSWORD,
                        collection_name=embedding_collection_name,
                    )
                    docs = retrieval.fetch_documents(query=query, top_k=top_k)

                if enable_history == 1:
                    chat_history = json.loads(history.get(limit=10))

                # prepare the prompt
                prompt = prepare_prompt(query, docs, chat_history)
                print(f"prompt :{prompt}")

                response = invoke_model(prompt, max_tokens_to_sample)
                print(f"response :{response}")

                if enable_history == 1:
                    history.add(human_message=query, assistant_message=response)

        lex_response = prepare_lex_response(response, intent)
        return lex_response
    except Exception as e:
        print(e)
        return prepare_lex_response("Sorry, an error has happened.", intent)
