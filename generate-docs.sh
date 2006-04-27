#!/bin/sh

echo "This requires Epydoc (http://epydoc.sf.net) and DocUtils (http://docutils.sf.net)"

API_DIR=./share/docs/api/

MODULES="$@"
if [ x$MODULES = x ]; then
    MODULES="gtk maemo"
fi

export ORIGPYTHONPATH=$PYTHONPATH

for m in $MODULES; do
    cd $m
    export PYTHONPATH=$ORIGPYTHONPATH:$PWD
    echo $PWD >> /tmp/pythonpaths
    rm -fr $API_DIR
    mkdir -p $API_DIR
    epydoc --html \
	-o $API_DIR \
	--name="Eagle" \
	--url="http://code.gustavobarbieri.com.br/eagle/" \
	eagle
    cd ..
done
