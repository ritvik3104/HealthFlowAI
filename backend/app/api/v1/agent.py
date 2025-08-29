from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.schemas.prompt import PromptCreate, PromptResponse
from app.schemas.prompt_history import PromptHistoryCreate, PromptHistory
from app.services import llm_service
from app.models.user import User
from app.services import auth_service
from app.crud import crud_prompt_history
from app.api.v1.auth import get_db

router = APIRouter()

@router.post("/prompt", response_model=PromptResponse)
def handle_agent_prompt(
    prompt_data: PromptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Receives a user prompt, passes it to the LLM agent,
    and saves the conversation to the history. Includes robust error handling.
    """
    try:
        # Step 1: Get the agent's response
        result_dict = llm_service.process_prompt(
            prompt=prompt_data.prompt_text,
            current_user=current_user
        )
        
        if "error" in result_dict:
             raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=result_dict["error"],
            )

        final_response = result_dict.get("response")
        if not final_response:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="LLM service returned an unexpected data structure.",
            )

        # Step 2: Save the conversation to the database
        history_to_create = PromptHistoryCreate(
            prompt_text=prompt_data.prompt_text,
            response_text=final_response
        )
        crud_prompt_history.create_prompt_history(
            db=db,
            history_in=history_to_create,
            user_id=current_user.id
        )

        return PromptResponse(response=final_response)

    except Exception as e:
        # This is the crucial addition: Catch ANY other unexpected error
        # from the llm_service and return a proper 500 error.
        print(f"An unexpected error occurred in the agent endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred in the AI agent: {str(e)}",
        )

@router.get("/history", response_model=List[PromptHistory])
def get_user_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Retrieve all past prompt/response conversations for the currently logged-in user.
    """
    history = crud_prompt_history.get_prompt_history_by_user(db, user_id=current_user.id)
    return history
