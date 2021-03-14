all: signing-key.rsa signing-key.pem

signing-key.rsa:
	openssl genrsa -out signing-key.rsa 2048

signing-key.pem: signing-key.rsa
	openssl req -x509 -new -nodes -days 36500 -key signing-key.rsa -sha256 -out signing-key.pem -subj "/CN=test/"

.PHONY: signature
signature: data signing-key.rsa
	openssl dgst -sha1 -sign signing-key.rsa data | base64 -w 0
