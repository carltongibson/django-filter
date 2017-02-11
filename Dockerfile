FROM carlton/django-docker-testing:dev

RUN mkdir /src
WORKDIR /src
ADD . /src/

# Whilst .gitignored we may be using pyenv locally...
RUN if [ -f .python-version ] ; then rm .python-version; fi

CMD ["tox"]


