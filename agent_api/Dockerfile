FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy
WORKDIR /workspace
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn","agent_api.main:app","--host","0.0.0.0","--port","8000"]
