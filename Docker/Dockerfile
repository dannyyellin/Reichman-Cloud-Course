FROM python:alpine3.17
# This Dockerfile is for use with rest-word-svr-v1.py
# use Dockerfile.setport for rest-word-svr-v2.py
# make ./app the directory in the container for container files
WORKDIR ./app
COPY rest-word-svr-v1.py .
RUN pip install flask
RUN pip install flask_restful
# this is the port that the container will expose to restsvr.
EXPOSE 8000

CMD ["python3", "rest-word-svr-v1.py"]
