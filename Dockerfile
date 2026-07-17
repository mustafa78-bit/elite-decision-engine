FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import http.client; conn=http.client.HTTPConnection('localhost:8000'); conn.request('GET','/health'); resp=conn.getresponse(); exit(0) if resp.status==200 else exit(1)"

CMD ["python", "app.py"]
