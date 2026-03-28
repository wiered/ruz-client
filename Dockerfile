FROM python:3.12-slim

WORKDIR /ruz-client

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/ruz-client/src

COPY pyproject.toml .
COPY src ./src

RUN pip install --no-cache-dir aiohttp python-dotenv "pyTelegramBotAPI==4.32.0"

CMD ["python", "-m", "ruzbot.main"]
