FROM clamav/clamav:stable@sha256:12177441d1b40cef3c47b44c4090d59d4babc4c67bedd5af0fa315e603aa6dd8
RUN apk add --no-cache --upgrade libxml2
