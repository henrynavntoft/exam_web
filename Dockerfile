FROM python:3.10.5
WORKDIR /app
COPY req.txt /app
RUN pip install --no-cache-dir -r req.txt
COPY . .
CMD python app.py