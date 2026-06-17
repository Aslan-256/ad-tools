FROM python:3.11-slim

RUN pip install --no-cache-dir --upgrade pip

WORKDIR /exploit

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python3", "exploit.py" ]
