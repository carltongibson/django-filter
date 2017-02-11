FROM carlton/django-docker-testing:dev

RUN mkdir /src
WORKDIR /src
ADD . /src/
RUN rm .python-version

CMD ["tox"]


