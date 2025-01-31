from fastapi import FastAPI, File, UploadFile, HTTPException
import re
import os
import httpx
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI()

SINUS_TEST_PARSER = os.getenv('SINUS_TEST_PARSER', 'http://127.0.0.1:8005/')
XY_TEST_PARSER = os.getenv('XY_TEST_PARSER', 'http://127.0.0.1:8006/')

FILE_TYPE_PARSERS = {
    ("csv", "xy-test_.*"): XY_TEST_PARSER,
    ("txt", "SinusTest_.*"): SINUS_TEST_PARSER
}

logging.info(f"Parser: {FILE_TYPE_PARSERS}")

@app.post("/process-file")
async def process_file(file: UploadFile = File(...)):
    """
    Process the uploaded file to determine which parser should handle it and pass it there.
    """
    file_extension = file.filename.rsplit(".", 1)[-1].lower()
    file_name = file.filename.rsplit(".", 1)[0]

    for (extension, name_regex), parser_url in FILE_TYPE_PARSERS.items():
        if file_extension == extension and re.match(name_regex, file_name):
            assigned_parser_url = parser_url
            break
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_name+file_extension}. Supported types: {', '.join([str(x) for x in FILE_TYPE_PARSERS.keys()])}"
        )

    async with httpx.AsyncClient() as client:
        logger.info(f"URL for parser call: {assigned_parser_url}process-file")
        response = await client.post(
            f"{assigned_parser_url}process-file", 
            files={"file": (file_name, file.file, file.content_type)}
        )
    
    if response.status_code != 200:
        print(response.status_code, response.text)
        raise HTTPException(status_code=500, detail=f"Error in parser microservice: {response.json()}")

    return {
        "file_name": file_name,
        "file_extension": file_extension,
        "parser": parser_url,
        "message": f"The file {file_name} will be processed by {parser_url}.",
        "parser_response": response.json()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.2", port=5000, log_level="info")
