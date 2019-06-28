#!/bin/bash

##
## Copyright (c) 2019 SAP SE or an SAP affiliate company. All rights reserved.
##
## This file is part of ewm-cloud-robotics
## (see https://github.com/SAP/ewm-cloud-robotics).
##
## This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file (https://github.com/SAP/ewm-cloud-robotics/blob/master/LICENSE)
##



## self-signed-cert.sh can be used to distribute a self-signed certificate to enable communication 
## between order-manager and ewm-sim in cluster context
## (ref.: https://kubernetes.io/docs/concepts/cluster-administration/certificates/#distributing-self-signed-ca-certificate)

#########################################################################################
## UTILITIES

# trap ctrl-c and call ctrl_c()
trap ctrl_c INT
function ctrl_c() {
    printf "\n\nABORTED: Cleaning up.\n"
    cd ../ && rm -rf ./cert
    exit 0
}

function verify_kubectl_context {
    printf "kubectl is currently configured to: \n    "
    kubectl config current-context
    read -p "Do you want to proceed (Y/n):" ver
    
    if [[ $ver = "" ]] || [[ $ver = "Y" ]] || [[ $ver = "Yes" ]] || [[ $ver = "y" ]] || [[ $ver = "yes" ]]; then
        printf "\nOK\n\n"
    else
        cd ../ && rm -rf ./cert
        die "ABORTED: Please configure kubectl to use the correct context."
    fi
}

function verify_input {
    read -p "Please review output above. Do you want to proceed? (Y/n):" ver
    
    if [[ $ver = "" ]] || [[ $ver = "Y" ]] || [[ $ver = "Yes" ]] || [[ $ver = "y" ]] || [[ $ver = "yes" ]]; then
        printf "\nOK\n\n"
    else
        cd ../ && rm -rf ./cert
        die "ABORTED: No changes have been made."
    fi
}

function die {
    printf '\n%s\n' "$1" >&2
    exit 1
}

## UTILITIES
#########################################################################################
## MAIN

mkdir ./cert/ && cd ./cert

#############################################
## GET OPTIONS
verify_kubectl_context

printf "Currect cluster-info:\n"
kubectl cluster-info

read -p "Enter <MASTER_IP>:" MASTER_IP
printf "\nOK\n\n"

echo '
[ req ]
default_bits = 2048
prompt = no
default_md = sha256
req_extensions = req_ext
distinguished_name = dn

[ dn ]
C = US
ST = CA
L = SF
O = O
OU = U
CN = ${MASTER_IP}

[ req_ext ]
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = kubernetes
DNS.2 = kubernetes.default
DNS.3 = kubernetes.default.svc
DNS.4 = kubernetes.default.svc.cluster
DNS.5 = kubernetes.default.svc.cluster.local
DNS.6 = ewm-sim
IP.1 = ${MASTER_IP}

[ v3_ext ]
authorityKeyIdentifier=keyid,issuer:always
basicConstraints=CA:FALSE
keyUsage=keyEncipherment,dataEncipherment
extendedKeyUsage=serverAuth,clientAuth
subjectAltName=@alt_names
' > csr.conf

if [[ $(uname -s) = "Darwin" ]]; then
    sed -i '' -e 's#\${MASTER_IP}#'${MASTER_IP}'#' csr.conf
else
    sed -i -e 's#\${MASTER_IP}#'${MASTER_IP}'#' csr.conf
fi

printf "#################################################\n"
cat csr.conf

verify_input

#############################################
## CERTIFICATE GENERATION

## generate a ca.key with 2048bit:
openssl genrsa -out ca.key 2048
## according to the ca.key generate a ca.crt:
openssl req -x509 -new -nodes -key ca.key -subj "/CN=${MASTER_IP}" -days 10000 -out ca.crt
## generate a server.key with 2048bit:
openssl genrsa -out server.key 2048
## generate the certificate signing request based on the config file:
openssl req -new -key server.key -out server.csr -config csr.conf
## generate the server certificate using the ca.key, ca.crt and server.csr:
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key \
      -CAcreateserial -out server.crt -days 10000 \
      -extensions v3_ext -extfile csr.conf
## check out your certificate:
# openssl x509  -noout -text -in ./server.crt

#############################################
## CERTIFICATE DISTRIBUTION

cd ../
cp cert/server.key cert/key.pem
cp cert/server.crt cert/cert.pem

kubectl create configmap ewm-sim-cert --from-file=cert/ --dry-run=true -o yaml | kubectl apply -f -

rm -rf ./cert