FROM public.ecr.aws/docker/library/python:3.8-alpine3.13

RUN apk update \
    && apk --no-cache --update add \
    tzdata \
    build-base \
    openssl \
    openssl-dev \
    git \
    ttf-liberation \
    libreoffice \
    libressl-dev \
    libffi-dev \
    swig \
    libxml2 \
    libxml2-dev \
    libxslt-dev \
    postgresql-dev \
    jpeg-dev \
    zlib-dev \
    bash \
    nodejs \
    npm

RUN cp /usr/share/zoneinfo/America/Argentina/Buenos_Aires /etc/localtime
RUN echo America/Argentina/Buenos_Aires > /etc/timezone

COPY trytond/ /opt/tryton/trytond/
RUN pip install -r /opt/tryton/trytond/requirements.txt

WORKDIR /opt/tryton/trytond/sao
RUN npm install -g bower grunt-cli &&\
    npm install grunt-contrib-less --save-dev &&\
    npm install &&\
    bower install --allow-root &&\
#     npm install --prefix ./css/bootstrap/ &&\
#     grunt -b css/bootstrap dist &&\
    grunt

WORKDIR /opt/tryton/trytond
CMD python /opt/tryton/trytond/bin/trytond -c /opt/tryton/trytond/trytond.conf -v --logconf /opt/tryton/trytond/trytondlogs.conf
EXPOSE 8000
VOLUME ["/opt/tryton/trytond/log"]
VOLUME ["/opt/tryton/trytond/attachments"]