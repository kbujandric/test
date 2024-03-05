"""Tools for interacting with OpenAI's GPT-3, GPT-4 API"""
import asyncio
import random
import os
import time
import openai
from typing import List

HOST = os.getenv("OPENAI_API_BASE")
HOST_TYPE = os.getenv("BACKEND_TYPE")  # default None == ChatCompletion

if HOST is not None:
    openai.api_base = HOST

def retry_with_exponential_backoff(
    func,
    initial_delay: float = 1,
    exponential_base: float = 2,
    jitter: bool = True,
    max_retries: int = 20,
    errors: tuple = (openai.RateLimitError,),
):
    """Retry a function with exponential backoff."""

    def wrapper(*args, **kwargs):
        """Wrapper for sync functions."""
        # Initialize variables
        num_retries = 0
        delay = initial_delay

        # Loop until a successful response or max_retries is hit or an exception is raised
        while True:
            try:
                return func(*args, **kwargs)

            # Retry on specified errors
            except errors:
                # Increment retries
                num_retries += 1

                # Check if max retries has been reached
                if num_retries > max_retries:
                    raise Exception(
                        f"Maximum number of retries ({max_retries}) exceeded."
                    )

                # Increment the delay
                delay *= exponential_base * (1 + jitter * random.random())

                # Sleep for the delay
                time.sleep(delay)

            # Raise exceptions for any errors not specified
            except Exception as e:
                raise e

    return wrapper


@retry_with_exponential_backoff
def completions_with_backoff(**kwargs):
    """Wrapper around ChatCompletion.create w/ backoff"""
    # Local model
    return openai.chat.completions.create(**kwargs)


def aretry_with_exponential_backoff(
    func,
    initial_delay: float = 1,
    exponential_base: float = 2,
    jitter: bool = True,
    max_retries: int = 20,
    errors: tuple = (openai.RateLimitError,),
):
    """Retry a function with exponential backoff."""

    async def wrapper(*args, **kwargs):
        """Wrapper for async functions.
        :param args: list
        :param kwargs: dict"""
        # Initialize variables
        num_retries = 0
        delay = initial_delay

        # Loop until a successful response or max_retries is hit or an exception is raised
        while True:
            try:
                return await func(*args, **kwargs)

            # Retry on specified errors
            except errors as e:
                print(f"acreate (backoff): caught error: {e}")
                # Increment retries
                num_retries += 1

                # Check if max retries has been reached
                if num_retries > max_retries:
                    raise Exception(
                        f"Maximum number of retries ({max_retries}) exceeded."
                    )

                # Increment the delay
                delay *= exponential_base * (1 + jitter * random.random())

                # Sleep for the delay
                await asyncio.sleep(delay)

            # Raise exceptions for any errors not specified
            except Exception as e:
                raise e

    return wrapper


@aretry_with_exponential_backoff
async def acompletions_with_backoff(**kwargs):
    """Wrapper around ChatCompletion.acreate w/ backoff"""
    return await openai.chat.completions.acreate(**kwargs)


@aretry_with_exponential_backoff
async def acreate_embedding_with_backoff(**kwargs):
    """Wrapper around Embedding.acreate w/ backoff"""

    client = openai.AsyncOpenAI(
        # This is the default and can be omitted
        api_key=os.environ.get("OPENAI_API_KEY"),
    )

    return await client.embeddings.create(**kwargs)


async def async_get_embedding_with_backoff(text, model="text-embedding-ada-002"):
    """To get text embeddings, import/call this function
    It specifies defaults + handles rate-limiting + is async"""
    text = text.replace("\n", " ")
    response = await acreate_embedding_with_backoff(input=[text], model=model)
    embedding = response.data[0].embedding
    return embedding


@retry_with_exponential_backoff
def create_embedding_with_backoff(**kwargs):
    """Wrapper around Embedding.create w/ backoff"""
    return openai.embeddings.create(**kwargs)


def get_embedding_with_backoff(text:str, model:str="text-embedding-ada-002"):
    """To get text embeddings, import/call this function
    It specifies defaults + handles rate-limiting
    :param text: str
    :param model: str
    """
    text = text.replace("\n", " ")
    response = create_embedding_with_backoff(input=[text], model=model)
    embedding = response.data[0].embedding
    return embedding



async def async_get_multiple_embeddings_with_backoff(texts: List[str], models: List[str]) :
    """To get multiple text embeddings in parallel, import/call this function
    It specifies defaults + handles rate-limiting + is async"""
    # Create a generator of coroutines
    coroutines = (async_get_embedding_with_backoff(text, model) for text, model in zip(texts, models))

    # Run the coroutines in parallel and gather the results
    embeddings = await asyncio.gather(*coroutines)

    return embeddings
