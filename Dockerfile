FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Keep the container alive on a loop (we will trigger the script via cron later)
CMD ["tail", "-f", "/dev/null"]