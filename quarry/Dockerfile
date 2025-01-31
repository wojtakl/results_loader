FROM python:3.13-slim
WORKDIR /app
COPY . /app/
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
ENV SINUS_TEST_PARSER=sinus_parser:5000
ENV XY_TEST_PARSER=127.0.0.1:8006
ENV MONGO_URI=mongodb://mongodb:27017
ENTRYPOINT ["uvicorn", "quarry:app"]
CMD ["--host", "0.0.0.0", "--port", "5000"]