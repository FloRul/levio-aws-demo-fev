import json
import os
import boto3
from langchain_community.embeddings import BedrockEmbeddings
from langchain_community.vectorstores.pgvector import PGVector
from botocore.exceptions import ClientError
from botocore.exceptions import NoCredentialsError, BotoCoreError
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import psycopg2


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


def delete_documents(filename: str):
    with psycopg2.connect(
        dbname=PGVECTOR_DATABASE,
        user=PGVECTOR_USER,
        password=PGVECTOR_PASSWORD,
        host=PGVECTOR_HOST,
        port=PGVECTOR_PORT
    ) as conn:
        with conn.cursor() as cur:
            sql_query = f"""
            DELETE FROM langchain_pg_embedding
            WHERE cmetadata->>'source' = %s;
            """
            print(f"Executing query: {sql_query}")
            print(f"With parameters: {filename}")
            cur.execute(sql_query, (filename,))
            deleted_rows = cur.rowcount
            print(f"Number of deleted rows: {deleted_rows}")
    return deleted_rows


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


def extract_content_from_pdf(file_path, file_name):
    print(f"Extracting content from {file_name}")
    loader = PyPDFLoader(file_path)
    docs = loader.load_and_split(
        text_splitter=RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=50))
    for doc in docs:
        doc.metadata['source'] = file_name
    return docs


OBJECT_CREATED = 'ObjectCreated'
OBJECT_REMOVED = 'ObjectRemoved'


def get_bucket_and_key(record):
    print(record)
    bucket = record["s3"]["bucket"]["name"]
    key = record["s3"]["object"]["key"]
    return bucket, key


def lambda_handler(event, context):
    print(event)
    records = json.loads(event['Records'][0]['body'])['Records']
    for record in records:
        eventName = record['eventName']
        print(f"eventName: {eventName}")
        try:
            bucket, key = get_bucket_and_key(record)
            print(f"source_bucket: {bucket}, source_key: {key}")

            vector_store = get_vector_store(collection_name=bucket)

            if eventName.startswith(OBJECT_CREATED):
                local_filename, file_extension, file_name = fetch_file(
                    bucket, key)
                print(f"local_filename: {local_filename}")

                if file_extension == 'pdf':
                    print("Extracting text from pdf")
                    docs = extract_content_from_pdf(
                        local_filename, file_name=file_name)
                    vector_store.add_documents(docs)
                    print(f"Extracted {len(docs)} text")
                    return len(docs)

            elif eventName.startswith(OBJECT_REMOVED):
                return delete_documents(filename=key)

        except Exception as e:
            print(e)
            raise e
