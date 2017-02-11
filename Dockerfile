FROM python:3.6


RUN mkdir /src
WORKDIR /src
ADD . /src/

RUN pip install tox
RUN tox -e py36-djangolatest-restframeworklatest
