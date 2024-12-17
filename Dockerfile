FROM python:3.12-alpine
COPY .env.local requirements.txt ./
RUN mkdir ./src; pip install -r requirements.txt
#CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0"]
CMD ["python", "src/main.py"]