from fastapi import FastAPI, File, HTTPException, UploadFile
from pymongo import MongoClient
from bson.objectid import ObjectId
import json
import numpy as np
import traceback
import matplotlib.pyplot as plt
import mpld3
import os

app = FastAPI()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["test_results_db"]  # Database name
collection = db["test_results"]  # Collection name


@app.post("/process-file")
async def process_file(file: UploadFile = File(...)):
    file_content = await file.read()
    file_content_str = file_content.decode("utf-8")

    context, time, measurements = file_content_str.split(";")
    context = json.loads(context)
    time = np.array(time.split(",")).astype(float)
    measurements = np.array(measurements.split(",")).astype(float)

    distances = measurements - np.sin(2*np.pi*context["frequency"]*time/1000)
    average_noise = np.abs(distances).mean()

    result = collection.insert_one({
                                    "test_type": "sinus",
                                    "file_name": file.filename,
                                    "time": time.tolist(),
                                    "order_number": context["order_number"],
                                    "context": context,
                                    "measurements": measurements.tolist(),
                                    "test_passed": bool(average_noise < 0.2)})

    return {
        "status": "success",
        "message": f"File '{file.filename}' processed successfully.",
        "average_noise": average_noise,
        "test_passed": bool(average_noise < 0.2),
        "inserted_id": str(result.inserted_id),
    }

@app.get("/process_data")
def process_data(test_id: str):
    """
    Process data for a given test result by its BSON ID.
    """
    print("Test_id = "+test_id)
    try:
        result = collection.find_one({"_id": ObjectId(test_id)})
        if not result:
            raise HTTPException(status_code=404, detail="Test result not found")

        assert result.get("test_type") == "sinus", "Wrong parser for selected result."
        time = np.array(result.get("time")).astype(float)
        measurements = np.array(result.get("measurements")).astype(float)
        context = result.get("context")

        distances = measurements - np.sin(2*np.pi*context["frequency"]*time/1000)
        average_noise = np.abs(distances).mean()

        return {
            "test_id": test_id,
            "test_type": "sinus",
            "average_noise": average_noise,
            "test_passed": bool(average_noise < 0.2),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing data: {str(e), traceback.format_exc()}")

@app.get("/generate_plot")
def generate_plot(test_id: str):
    """
    Process data for a given test result by its BSON ID.
    """
    print("Test_id = "+test_id)
    try:
        result = collection.find_one({"_id": ObjectId(test_id)})
        if not result:
            raise HTTPException(status_code=404, detail="Test result not found")

        assert result.get("test_type") == "sinus", "Wrong parser for selected result."
        time = np.array(result.get("time")).astype(float)
        measurements = np.array(result.get("measurements")).astype(float)
        context = result.get("context")

        plt.plot(time, measurements)
        html_content = mpld3.fig_to_html(plt.gcf())

        return {
            "test_id": test_id,
            "test_type": "sinus",
            "plot_html": html_content,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing data: {str(e), traceback.format_exc()}")
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8005, log_level="info")
