# GNU Wget

GNU Wget 1.25.0 is included in the console and desktop profiles for x86 and
x64. The package provides `/usr/bin/wget` with HTTP, HTTPS, and FTP support.
OpenSSL supplies TLS, libidn2 supplies internationalized domain names, libpsl
supplies public-suffix checking, and PCRE2 supplies regular expressions.
Zlib supports compressed HTTP responses, and libuuid supports WARC identifiers.

The `ca-certificates` package installs the Mozilla server-authentication trust
anchors from ca-certificates 20260816. The PEM bundle resides at
`/etc/ssl/certs/ca-certificates.crt`; `/etc/ssl/cert.pem` links to this bundle
for the configured OpenSSL default certificate file.

```sh
wget https://www.gnu.org/
wget -O archive.tar.gz https://example.org/archive.tar.gz
```
