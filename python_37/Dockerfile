FROM python:3.7.3-slim-stretch
LABEL maintainer="JINWOO <jinwoo@iconloop.com>"
ENV TZ "Asia/Seoul"
ENV TERM "xterm-256color"
ENV USERID 24988
ENV APP_DIR "jtools"
ARG APP_VERSION
ARG VERSION
ARG NAME
ARG IS_BUILDER
ARG IS_LOCAL
ENV IS_DOCKER "true"
ENV IS_BUILDER=$IS_BUILDER
ENV APP_VERSION ${NAME}_${VERSION}
ENV RABBITMQ_VERSION $RABBITMQ_VERSION
ENV GO_VERSION $GO_VERSION
ENV DOCKERIZE_VERSION $DOCKERIZE_VERSION
ENV PATH /src:$PATH
# if you ignore certificate validation
#ENV PIP_TRUST_OPT "--trusted-host=pypi.org --trusted-host=pypi.python.org --trusted-host=files.pythonhosted.org"
COPY src /src
COPY src/pip.conf /etc/
RUN ln -s /usr/local/bin/python3.7 /usr/local/bin/python3.6
RUN mkdir -p /usr/share/man/man1 /usr/share/man/man7
ENV INSTALL_PACKAGE "make gcc libssl-dev  \
                   tk-dev libffi-dev liblzma-dev automake git g++"
#ENV MANDATORY_PACKAGE "libsecp256k1-dev pigz git curl pkg-config"
ENV MANDATORY_PACKAGE "libsecp256k1-dev pigz pkg-config curl libcurl4-openssl-dev"
ENV REMOVE_PACKAGE "gcc-6 libgl1-mesa-dri shared-mime-info gcc g++* g++-6* make git automake"
ENV UTIL_PACKAGE ""
RUN if [ "${IS_LOCAL}" = "true" ]; then \
        echo "-- KR mirror" ;\
#        sed -i.bak -re "s/([a-z]{2}.)?archive.ubuntu.com|security.ubuntu.com|deb.debian.org|security\-cdn.debian.org|security.debian.org/mirror.kakao.com/g" /etc/apt/sources.list; \
        sed -i.bak -re "s/([a-z]{2}.)?archive.ubuntu.com|security.ubuntu.com|deb.debian.org|security\-cdn.debian.org/mirror.kakao.com/g" /etc/apt/sources.list; \
    else \
        echo "-- Global mirror" ;\
        rm -f /etc/pip.conf ; \
    fi; \
    apt update &&  \
    apt install -y $INSTALL_PACKAGE $MANDATORY_PACKAGE $UTIL_PACKAGE && \
    pip install --upgrade pip && \
    pip3 install -r /src/requirements.txt &&\
    apt-get purge --yes --auto-remove -o APT::AutoRemove::RecommendsImportant=false -o APT::AutoRemove::SuggestsImportant=false $BUILD_PACKAGE  $UTIL_PACKAGE && \
    if [ "$IS_BUILDER" != "true" ]; then \
        apt autoremove -y $REMOVE_PACKAGE ; \
    fi; \
    rm -rf /root/.cache* && \
    rm -rf /var/lib/apt/lists/*
RUN mkdir -p $APP_DIR
RUN echo 'export PS1=" \[\e[00;32m\]${APP_VERSION}\[\e[0m\]\[\e[00;37m\]@\[\e[0m\]\[\e[00;31m\]\H :\\$\[\e[0m\] "' >> /root/.bashrc
#ENTRYPOINT [ "/src/sendme_log.py" ]
