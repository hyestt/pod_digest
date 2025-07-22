from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict
import httpx
from ..config import settings

router = APIRouter()


class SubscribeRequest(BaseModel):
    email: str
    name: str = ""
    utm_source: str = "website"
    utm_medium: str = "organic"


class SubscribeResponse(BaseModel):
    success: bool
    message: str
    subscriber_id: str = None


@router.post("/subscribe", response_model=SubscribeResponse)
async def subscribe_to_newsletter(request: SubscribeRequest):
    """Subscribe user to newsletter via Beehiiv API"""
    
    if not settings.beehiiv_api_key or not settings.beehiiv_publication_id:
        raise HTTPException(
            status_code=500, 
            detail="Newsletter service is not configured properly"
        )
    
    try:
        # Prepare Beehiiv API request
        headers = {
            "Authorization": f"Bearer {settings.beehiiv_api_key}",
            "Content-Type": "application/json"
        }
        
        # Beehiiv subscriber data
        subscriber_data = {
            "email": request.email,
            "reactivate_existing": True,
            "send_welcome_email": True,
            "utm_source": request.utm_source,
            "utm_medium": request.utm_medium
        }
        
        # Add name as custom field if provided
        if request.name.strip():
            subscriber_data["custom_fields"] = [
                {"name": "name", "value": request.name.strip()}
            ]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"https://api.beehiiv.com/v2/publications/{settings.beehiiv_publication_id}/subscriptions",
                json=subscriber_data,
                headers=headers
            )
            
            if response.status_code == 201:
                # Successful subscription
                data = response.json()
                return SubscribeResponse(
                    success=True,
                    message="Successfully subscribed to newsletter!",
                    subscriber_id=data.get("data", {}).get("id", "")
                )
            elif response.status_code == 400:
                # Handle common errors
                error_data = response.json()
                error_message = error_data.get("errors", [{}])[0].get("message", "Invalid email address")
                
                if "already exists" in error_message.lower():
                    return SubscribeResponse(
                        success=True,
                        message="You're already subscribed to our newsletter!"
                    )
                else:
                    raise HTTPException(status_code=400, detail=error_message)
            else:
                # Other HTTP errors
                response.raise_for_status()
                
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail="Newsletter service is temporarily unavailable. Please try again later."
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(
                status_code=500,
                detail="Newsletter service authentication failed"
            )
        elif e.response.status_code == 429:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again in a few minutes."
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Newsletter subscription failed. Please try again."
            )
    except Exception as e:
        print(f"Newsletter subscription error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred. Please try again."
        )


@router.get("/health")
async def newsletter_health_check():
    """Check if newsletter service is properly configured"""
    return {
        "status": "healthy",
        "beehiiv_configured": bool(settings.beehiiv_api_key and settings.beehiiv_publication_id),
        "service": "newsletter"
    }