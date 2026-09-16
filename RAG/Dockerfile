FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

# Install the CPU-only build of PyTorch first, from PyTorch's own package
# index. sentence-transformers depends on torch, and a plain `pip install`
# on Linux resolves to the GPU (CUDA) build by default - which drags in
# several GB of NVIDIA libraries we will never use (this app only ever
# does CPU inference; a free-tier EC2 instance has no GPU anyway).
# Installing the CPU wheel first satisfies that dependency before
# requirements.txt gets a chance to pull in the GPU version.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir -r requirements.txt

# Download and cache the embedding model INTO THE IMAGE now, at build
# time, while network access is available and expected. Without this,
# SentenceTransformer re-checks Hugging Face Hub for updates on every
# container cold start - which is slow, and makes startup depend on an
# external service being reachable. HF_HUB_OFFLINE is set *after* this
# download step (not before) so the app never makes that network call at
# runtime: it always uses the copy already cached in this image layer.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
ENV HF_HUB_OFFLINE=1

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]