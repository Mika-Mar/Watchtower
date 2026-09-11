FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python -c "from app.notifiers.bark import BarkNotifier"

CMD ["python", "main.py"]
