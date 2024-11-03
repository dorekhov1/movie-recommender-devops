FROM python:3.11-slim

WORKDIR /app

RUN pip install --upgrade pip

COPY fallback_solution/requirements.txt .
RUN pip install -r requirements.txt

COPY model/ model/
COPY fallback_solution/app.py .

EXPOSE 5000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000", "--workers", "4"]
