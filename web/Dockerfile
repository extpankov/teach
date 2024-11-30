
FROM python:3.12-slim


ENV PYTHONUNBUFFERED=1


WORKDIR /app


COPY requirements.txt /app/


RUN pip install --no-cache-dir -r requirements.txt


COPY . /app


#CMD ["flask", "run", "--host=0.0.0.0", "--port=5001"]
CMD ["python", "manage.py"]