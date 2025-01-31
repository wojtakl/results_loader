FROM python:3.13-slim
WORKDIR /app
COPY . /app/
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
ENV MONGO_URI=mongodb://localhost:27017
ENTRYPOINT ["uvicorn", "sinus_parser:app"]
CMD ["--host", "0.0.0.0", "--port", "5000"]