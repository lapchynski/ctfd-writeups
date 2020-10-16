FROM ctfd/ctfd

ENV PYTHONUNBUFFERED 1
ENTRYPOINT ["python", "serve.py"]