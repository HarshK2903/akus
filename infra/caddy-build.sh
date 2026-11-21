#!/bin/sh
# Compile the upstream standard Caddy command with patched Go dependencies.
set -eu
go mod init akus.local/caddy-build
go mod download github.com/caddyserver/caddy/v2@v2.11.9
cp /go/pkg/mod/github.com/caddyserver/caddy/v2@v2.11.9/cmd/caddy/main.go .
go get github.com/caddyserver/caddy/v2@v2.11.9 golang.org/x/net@v0.62.0 go.opentelemetry.io/otel/sdk@v1.47.0 go.opentelemetry.io/otel/trace@v1.47.0 go.opentelemetry.io/otel/sdk/log@v1.47.0 golang.org/x/crypto@v0.59.0
go mod tidy
go mod verify
CGO_ENABLED=0 go build -mod=readonly -p 2 -trimpath -o /out/caddy .
/out/caddy version
/out/caddy list-modules | grep -qx http.handlers.reverse_proxy
