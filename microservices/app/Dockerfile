FROM python:alpine3.17
# make ./app the directory in the container for container files
WORKDIR ./app
COPY rest-word-svr-v2.py .
RUN pip install flask
RUN pip install flask_restful
ENV FLASK_APP=rest-word-svr-v2.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=80

EXPOSE 80
CMD ["flask", "run"]
