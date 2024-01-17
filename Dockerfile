# FROM python:3.11.4
# RUN apt-get update -y && \
#     apt-get install -y python-pip python-dev
# WORKDIR /app
# COPY ./requirements.txt /app/requirements.txt 
# RUN pip install -r requirements.txt
# CMD ["python", :./app.py]
# CMD ["flask", "run", "app", "1.2.3.4"]

FROM python:3.11.4
EXPOSE 5000  
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD python ./app.py
