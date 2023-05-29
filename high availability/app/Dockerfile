FROM python:alpine3.17
# make ./app the directory in the container for container files
WORKDIR ./app
RUN pip install flask
RUN pip install flask_restful
RUN pip install pymongo
# RUN pip install simplejson
# Run pip install pickle4
ENV FLASK_APP=rest-word-svr-v3.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=80

COPY rest-word-svr-v3.py .
EXPOSE 80

CMD ["flask", "run"]
