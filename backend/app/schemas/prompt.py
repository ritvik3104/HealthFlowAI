from pydantic import BaseModel

class PromptCreate(BaseModel):
    """
    Schema for receiving a prompt from the user.
    """
    prompt_text: str

class PromptResponse(BaseModel):
    """
    Schema for sending a response back to the user.
    """
    response: str
