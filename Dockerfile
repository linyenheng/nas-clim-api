FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py data_sets.py ./
COPY return_water_levels.tar.gz ./

# 解壓縮資料
RUN mkdir -p data && \
    tar -xzf return_water_levels.tar.gz -C data/ && \
    rm return_water_levels.tar.gz

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
