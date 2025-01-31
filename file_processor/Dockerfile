FROM python:3.13-slim
WORKDIR /app
COPY . /app/
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
ENV SINUS_TEST_PARSER=http://sinus_parser:5000/process-file
ENV XY_TEST_PARSER=http://127.0.0.1:8006/process-file
CMD ["uvicorn", "file_processor:app", "--host", "0.0.0.0", "--port", "5000"]