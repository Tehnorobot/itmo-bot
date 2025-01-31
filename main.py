import time
from typing import List

from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import HttpUrl
from app.request import PredictionRequest, PredictionResponse
from app.tools.search_tool import process_query
import logging

# Initialize
app = FastAPI()

logger = logging.getLogger(__name__)

logger.setLevel(logging.NOTSET)
logging.basicConfig(level=logging.NOTSET) 



@app.post("/api/request", response_model=PredictionResponse)
async def predict(body: PredictionRequest):
    print('*****')
    try:
        logger.info(f"Processing prediction request with id: {body.id}")

        if not body.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        # Здесь будет вызов вашей модели
        json_ans = process_query(body.query)

        response = PredictionResponse(
            id=body.id,
            answer=json_ans.get('answer'),
            reasoning=json_ans.get('reasoning', ''),
            sources=json_ans.get('urls', []),
        )
        logger.info(f"Successfully processed request {body.id}")
        return response
    except ValueError as e:
        error_msg = str(e)
        logger.error(f"Validation error for request {body.id}: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        logger.error(f"Internal error processing request {body.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")