from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.config import Settings, get_settings

router = APIRouter()


class ContactFormRequest(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str
    workspace_invite_code: Optional[str] = None
    botcheck: Optional[str] = None


class ContactFormResponse(BaseModel):
    success: bool
    message: str


@router.post("/contact", response_model=ContactFormResponse, status_code=status.HTTP_200_OK)
async def submit_contact_form(
    data: ContactFormRequest,
    settings: Settings = Depends(get_settings),
):
    """Forward a contact/feedback form to Web3Forms.

    This lets the project use Web3Forms' free tier for form submissions
    without running an SMTP server. The access key is configured via
    WEB3FORMS_ACCESS_KEY in the environment.
    """
    if not settings.is_web3forms_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Web3Forms integration is not configured",
        )

    payload = {
        "access_key": settings.web3forms_access_key,
        "name": data.name,
        "email": str(data.email),
        "subject": f"[TaskFlow] {data.subject}",
        "message": data.message,
        "from_name": "TaskFlow Contact Form",
    }
    if data.workspace_invite_code:
        payload["workspace_invite_code"] = data.workspace_invite_code
    if data.botcheck:
        payload["botcheck"] = data.botcheck

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(settings.web3forms_endpoint, json=payload)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Web3Forms returned an error: {exc.response.status_code}",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach Web3Forms",
        ) from exc

    return ContactFormResponse(success=True, message="Form submitted successfully")
