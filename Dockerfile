FROM python:3.11-slim

WORKDIR /app

# sentence-transformers pulls in CUDA-enabled torch by default, adding several
# GB of unused GPU libraries to an image that only ever runs on CPU. Installing
# the CPU-only build first satisfies that dependency before pip gets to it.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY data/raw/ data/raw/
COPY evals/ evals/

RUN python -m src.ingest \
    && python -m src.chunk \
    && python -m src.embed

CMD ["python", "-m", "src.cli"]
