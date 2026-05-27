
from typing import List
from pydantic import BaseModel
from eApp.config import CONFIG
from langchain_groq import ChatGroq

model_name = "llama-3.1-8b-instant"

class AgentState(BaseModel):
    user_question: str 
    current_user_id : int 
    accumulated_info: List[str] = []
    generated_content: str = ""
    pass 


