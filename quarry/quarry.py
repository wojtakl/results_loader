import os
from fastapi import FastAPI, File, HTTPException, UploadFile
import httpx
from pymongo import MongoClient
from bson.objectid import ObjectId
import json
import traceback
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["test_results_db"]  # Database name
collection = db["test_results"]  # Collection name

SINUS_TEST_PARSER = os.getenv('SINUS_TEST_PARSER', 'http://127.0.0.1:8005/')
XY_TEST_PARSER = os.getenv('XY_TEST_PARSER', 'http://127.0.0.1:8006')

PARSERS_URL = {
    "sinus": SINUS_TEST_PARSER,
    "xy": XY_TEST_PARSER
}

@app.get("/find_result/{order_number}")
async def find_result(order_number: str):
    try:
        # Retrieve the document from MongoDB
        result = collection.find_one({"order_number": int(order_number)})
        if not result:
            raise HTTPException(status_code=404, detail=f"Test result not found for {order_number=}")

        return {
            "test_type": result.get("test_type"),
            "result_id": str(result.get("_id")),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing data: {str(e), traceback.format_exc()}")
    
@app.get("/find_results/{order_number}")
async def find_results(order_number: str):
    try:
        results = collection.find({"order_number": int(order_number)})
        if not results:
            raise HTTPException(status_code=404, detail=f"Test results not found for {order_number=}")

        return [{"test_type": result.get("test_type"), "result_id": str(result.get("_id"))} for result in results]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing data: {str(e), traceback.format_exc()}")
    
@app.get("/get-processed-data/{order_number}")
async def get_processed_data(order_number: str):
    try:
        result = await find_result(order_number)

        async with httpx.AsyncClient() as client:
            print(result["result_id"])
            response = await client.get(f"{PARSERS_URL[result['test_type']]}/process_data", params={"test_id": result["result_id"]})

        if response.status_code != 200:
            print(response)
            raise HTTPException(status_code=500, detail=f"Failed to retrieve processed data: {response.text}")

        return response.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing data: {str(e), traceback.format_exc()}")
    
@app.get("/get-plot/{result_id}")
async def get_plot(result_id: str):
    try:
        result = collection.find_one({"_id": ObjectId(result_id)})
        logger.info("Result found.")

        async with httpx.AsyncClient() as client:
            logger.info(f"Result: {result}")
            url = f"{PARSERS_URL[result['test_type']]}generate_plot"
            logger.info(f"URL for the call {url}")
            response = await client.get(url, params={"test_id": result.get("_id")})
            logger.info(f"Final request URL: {response.request.url}")

        if response.status_code != 200:
            logger.info(f"Request failed: {response}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve processed data: {response.text}")

        return response.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing data: {str(e), traceback.format_exc()}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
