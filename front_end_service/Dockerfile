FROM python:3.13-slim
WORKDIR /app
COPY . /app/
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
ENV FILE_PROCESSOR_URL=http://file_processor:5000/process-file
ENV QUARRY_URL=http://quarry:5000/
ENV FLASK_APP=front_end_service.py
ENTRYPOINT ["flask"]
CMD ["run", "--host=0.0.0.0", "--port=5000"]