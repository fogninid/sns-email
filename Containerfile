FROM debian:trixie AS build

RUN apt-get update \
    && \
    apt-get install -y --no-install-recommends \
       python3 python3-pip python3-venv \
       make \
    && \
    apt-get clean && rm -rf /var/lib/apt/lists/*


COPY . /src

WORKDIR /src

RUN make test PYENV=/app/sns-email/

RUN /app/sns-email/bin/pip install /src


FROM debian:trixie

RUN apt-get update \
    && \
    apt-get install -y --no-install-recommends \
       python3 \
    && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=build /app/sns-email/ /app/sns-email/

RUN groupadd -g 1000 sns-email && useradd -g 1000 -u 1000 -M sns-email

USER 1000

EXPOSE 10000

ENTRYPOINT ["/app/sns-email/bin/sns-email"]
