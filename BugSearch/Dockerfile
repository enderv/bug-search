FROM python:2.7

RUN mkdir -p /usr/src/
WORKDIR /usr/src/

COPY ./bug-search-code/requirements.txt /usr/src/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/src/
ENV PYTHON_ENV=docker
CMD [ "python", "/usr/src/bug-search-code/app/__init__.py"]