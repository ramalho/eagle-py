#!/bin/sh

echo "This requires Epydoc (http://epydoc.sf.net) and DocUtils (http://docutils.sf.net)"

API_DIR=./docs/api/
MODULES="eagle"

export PYTHONPATH=$PYTHONPATH:.

rm -fr $API_DIR
mkdir -p $API_DIR
epydoc --html \
    -o $API_DIR \
    -n "Eagle" \
    -u "http://code.gustavobarbieri.com.br/eagle/" \
    $MODULES

