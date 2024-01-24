FROM python:3.9.10
WORKDIR /srv
RUN pip install --upgrade pip
RUN pip install flask
RUN pip install Flask-SQLAlchemy 
RUN pip install Flask-Mail
RUN pip install Flask-Migrate
RUN pip install pytz
RUN pip install pandas
RUN pip install Flask-Bootstrap
RUN pip install openpyxl
RUN pip install boto3
COPY . /srv
ENV FLASK_APP=app
CMD ["python","app.py"]