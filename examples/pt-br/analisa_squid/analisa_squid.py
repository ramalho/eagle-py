#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from eagle import *
import webbrowser
from operator import itemgetter

lista = []

def abreArquivo(app, button, nomeArquivo):
    "Abre arquivo e o lê para uma lista"
    if not nomeArquivo:
        error("Defina o nome do arquivo de log a ser lido!")
        app["nomeArquivo"] = "Arquivo log: "
        return
    else:
        app["nomeArquivo"] = "Arquivo log: %s" % nomeArquivo

    arquivo = open(nomeArquivo, "r")
    linhas = arquivo.readlines() # lê o conteúdo do arquivo em linhas
    arquivo.close()

    global lista
    lista = linhas

    preencheTabela(app)


def preencheTabela(app):
    sites = {}
    nrLinhas = 0
    tipoLog = app["tipoLog"]

    if not tipoLog or not lista:
        return

    for linha in lista:
        if tipoLog in linha:
            try:
                inicio = linha.index("//")
                fim = linha.index("/", inicio + 2)
            except ValueError, e:
                continue

            nrLinhas += 1

            site = linha[inicio + 2 : fim]
            if site in sites:
                sites[site] += 1
            else:
                sites[site] = 0

    app["nrLinhas"] = nrLinhas
    app["nrEnderecos"] = len(sites)

    listaSitesOrdenada = sorted(sites.iteritems(),
                                key=itemgetter(1),
                                reverse=True)

    tabela = app["enderecos"]
    del tabela[:] # limpa conteúdo da tabela

    for endereco, acessos in listaSitesOrdenada:
        tabela.append((endereco, int(acessos)))
    tabela.select(0)


def geraRelatorio(app, button, nomeRelatorio):
    "Gera relatório em HTML"

    if not nomeRelatorio:
        error("Defina o nome do relatório!")
        app["nomeArquivo"] = "Nome do relatório: "
        return
    else:
        app["nomeArquivo"] = "Nome do relatório: %s" % nomeRelatorio

    arquivo = open(nomeRelatorio, "w")
    arquivo.write("""\
<html>
  <head>
    <title>Relat&oacute;rio de An&aacute;lise de Log do Squid</title>
  </head>
  <body>
    <h4>Relat&oacute;rio de log do Squid</h4>
    <table border="9" bgcolor="FFFFFF">
      <thead>
        <tr>
          <td>Endere&ccedil;os:</td>
          <td>Quantidade de Acessos:</td>
        </tr>
      </thead>
      <tbody>
""")

    for site, acessos in app["enderecos"]:
        arquivo.write("""\
        <tr>
          <td><a href="http://%(site)s">%(site)s</a></td>
          <td>%(acessos)s</td>
        </tr>
""" % {"site": site, "acessos": acessos})

    arquivo.write("""\
      </tbody>
    </table>
  </body>
</html>
""")
    arquivo.close()
    webbrowser.open_new("file://" + nomeRelatorio)


def mudaTipo(app, wid, value):
    preencheTabela(app)


app = App(title="Analisador de logs do Squid",
          author="Roberto",
          help="Analisa logs do Squid e permite salvar relatórios HTML.",
          top=(OpenFileButton(filter=["*.log", "*.*"],
                              callback=abreArquivo),
               SaveFileButton(filter=["text/html", "*.*"],
                              callback=geraRelatorio),
               Label(id="nomeArquivo",
                     label="Arquivo de log:"),
               ),
          right=(Selection(id="tipoLog",
                           label="Tipo log:",
                           options=["MISS", "DENIED", "HIT"],
                           persistent=True,
                           callback=mudaTipo),
                 Entry(id="nrLinhas",
                       label="Número de linhas:",
                       editable=False),
                 Entry(id="nrEnderecos",
                       label="Número de endereços:",
                       editable=False),
                 ),
          center=(Table(id="enderecos",
                        label="Endereços: ",
                        headers=("Endereço", "Acessos"),
                        types=(str, int),
                        expand_columns_indexes=(0,),
                        ),
                  ),
          )

run()
