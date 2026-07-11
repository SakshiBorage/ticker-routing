import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
SUMMARY_MODEL_NAME = "gpt-4o-mini"
TOKEN_THRESHOLD = 300  # tickets at or under this token count pass through unchanged

llm = ChatOpenAI(
    model=MODEL_NAME,
    temperature=0,
)

summarizer_llm = ChatOpenAI(
    model=SUMMARY_MODEL_NAME,
    temperature=0,
)
