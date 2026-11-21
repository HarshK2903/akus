FROM golang:1.27.4-alpine@sha256:70bd7ddea8b6cbe5d6943cde279d6b67feb10cc924fb9100d1d8757c1575b280 AS helper
WORKDIR /src
ADD --checksum=sha256:207a2045e890d3ca3326027c5f585733085960b401a49dbc00e3bb628c054cf8 https://codeload.github.com/tianon/gosu/tar.gz/refs/tags/1.20 /tmp/gosu.tar.gz
RUN tar xzf /tmp/gosu.tar.gz --strip-components=1 && go mod download && go mod verify && CGO_ENABLED=0 go build -mod=readonly -trimpath -o /out/gosu . && go version -m /out/gosu

FROM postgres:16@sha256:3950ad7c3148ca2175ef1b6c36c9efbf78957ae8fbe8b3a5d7c35af50500382f
RUN apt-get update && apt-get install -y --no-install-recommends --only-upgrade zlib1g libxml2 && rm -rf /var/lib/apt/lists/*
COPY --from=helper /out/gosu /usr/local/bin/gosu
RUN gosu --version && test "$(gosu postgres id -u)" = "$(id -u postgres)"
