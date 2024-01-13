import json
import os
import boto3
from langchain_community.embeddings import BedrockEmbeddings
from langchain_community.vectorstores.pgvector import PGVector
from botocore.exceptions import ClientError
from botocore.exceptions import NoCredentialsError, BotoCoreError
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter


def fetch_file(bucket, key):
    s3 = boto3.client('s3')
    # Extract file extension from key
    file_extension = os.path.splitext(key)[1][1:]
    file_name = os.path.splitext(key)[0]
    local_filename = f'/tmp/{file_name}.{file_extension}'
    try:
        s3.download_file(bucket, key, local_filename)
    except NoCredentialsError as e:
        print(e)
        raise e
    except BotoCoreError as e:
        print(e)
        raise e
    except ClientError as e:
        print(e)
        raise e
    return local_filename, file_extension, file_name


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


def get_connection_string():
    PGVECTOR_DRIVER = os.environ.get("PGVECTOR_DRIVER", "psycopg2")
    PGVECTOR_HOST = os.environ.get("PGVECTOR_HOST", "localhost")
    PGVECTOR_PORT = int(os.environ.get("PGVECTOR_PORT", 5432))
    PGVECTOR_DATABASE = os.environ.get("PGVECTOR_DATABASE", "postgres")
    PGVECTOR_USER = os.environ.get("PGVECTOR_USER", "postgres")
    PGVECTOR_PASSWORD = get_secret()
    CONNECTION_STRING = PGVector.connection_string_from_db_params(
        driver=PGVECTOR_DRIVER,
        host=PGVECTOR_HOST,
        port=PGVECTOR_PORT,
        database=PGVECTOR_DATABASE,
        user=PGVECTOR_USER,
        password=PGVECTOR_PASSWORD,
    )
    return CONNECTION_STRING


def get_vector_store():
    bedrock = boto3.client('bedrock-runtime')
    return PGVector(connection_string=get_connection_string(),
                    collection_name="main_connection",
                    embedding_function=BedrockEmbeddings(client=bedrock))


def extract_content_from_pdf(file_path, file_name):
    print(f"Extracting content from {file_name}")
    loader = PyPDFLoader(file_path)
    docs = loader.load_and_split(
        text_splitter=RecursiveCharacterTextSplitter(chunk_size=450, chunk_overlap=0))
    return docs


def lambda_handler(event, context):
    for record in event['Records']:
        sqs_event = json.loads(record['body'])
        print(f"SQS event: {sqs_event}")
        source_bucket = sqs_event["Records"][0]["s3"]["bucket"]["name"]
        source_key = sqs_event["Records"][0]["s3"]["object"]["key"]
        print(f"source_bucket: {source_bucket}")
        print(f"source_key: {source_key}")
        vector_store = get_vector_store()
        print("vector store retrieved")
        local_filename, file_extension, file_name = fetch_file(
            source_bucket, source_key)
        print(f"local_filename: {local_filename}")

        if file_extension == 'pdf':
            print("Extracting text from pdf")
            docs = extract_content_from_pdf(
                local_filename, file_name=file_name)
            vector_store.add_documents(docs)
            print(f"Extracted {len(docs)} text")

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
