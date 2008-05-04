#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Lista de Compras by Rafaela Schaldach & Bianca Brasil - BSI 310

from eagle import *
from decimal import Decimal
import os
import codecs
import webbrowser

mudancas = False
status_messages = []

def le_tabela(table, nome_arquivo):
    del table[:]

    arquivo = codecs.open(nome_arquivo, "r", encoding="utf-8")
    for ln, linha in enumerate(arquivo):
        try:
            if linha.endswith('\n'):
                linha = linha[:-1]
                categoria, descricao, quantidade, preco = linha.split(";")
                table.append((categoria, descricao, int(quantidade),
                              Decimal(preco)),
                             select=False, autosize=False)
        except Exception, e:
            error("Erro processando linha %d, %r: %s" % (ln, linha, e))

    arquivo.close()
    table.columns_autosize()
# le_tabela()


def salva_tabela(table, nome_arquivo):
    arquivo = codecs.open(nome_arquivo, "w", encoding="utf-8")
    for n, (categoria, descricao, quantidade, preco) in enumerate(table):
        if not (categoria and descricao):
            error("linha inválida %d pulada" % n)
            continue

        arquivo.write("%s;%s;%s;%s\n" %
                      (categoria, descricao, quantidade, preco))
    arquivo.close()
# salva_tabela()


def define_sem_mudancas(app):
    for i in status_messages:
        app.remove_status_message(i)
    del status_messages[:]

    global mudancas
    mudancas = False
    set_inactive("save", app)
# define_sem_mudancas()


def define_nome_arquivo(app, nome_arquivo=None):
    if nome_arquivo:
        app["nome_arquivo"] = "Arquivo: %s" % nome_arquivo
    else:
        app["nome_arquivo"] = "Nenhum arquivo selecionado!"
# define_nome_arquivo()


def escolhe_arquivo(app, button, nome_arquivo):
    if mudancas:
        msg = "Ainda existem dados não salvos! Continuar e descartá-los?"
        if not yesno(msg):
            return

    define_nome_arquivo(app, nome_arquivo)
    if nome_arquivo:
        le_tabela(app["lista"], nome_arquivo)
        define_sem_mudancas(app)
# escolhe_arquivo()


total = 0
def dados_alterados(app, table, data):
    global mudancas, total

    mudancas = True
    status_messages.append(app.status_message("Mudanças ainda não salvas!"))
    set_active("save", True, app)
    total=0
    for linha in table:
        total += (linha[2] * linha[3])
    app["total"] = "R$ %0.2f" %total
# dados_alterados()


def salva_arquivo(app, button):
    nome_arquivo = None
    while nome_arquivo is None:
        nome_arquivo = app.file_chooser(FileChooser.ACTION_SAVE)
    define_nome_arquivo(app, nome_arquivo)
    salva_tabela(app["lista"], nome_arquivo)
    define_sem_mudancas(app)
# salva_arquivo()


def quit(app):
    if mudancas:
        return yesno("Ainda existem dados não salvos!"
                     "Continuar e descartá-los?")
    else:
        return True
# quit()


def gera_relatorio(app, table):
    caminho = os.path.abspath(app["nome_relatorio"])
    arquivo = open(caminho, "w")
    arquivo.write("""\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
            "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
   <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
   <title>Lista de Compras</title>
</head>
<body>
   <center>
      <table width="900" border="0">
         <thead>
            <tr>
               <td><img src="carrinho.jpg"></td>
               <td colspan=3 align="center"><h1>Lista de Compras</h1></td>
            </tr>
            <tr>
               <td><h3>Categoria:</td>
               <td><h3>Descrição:</td>
               <td align="right"><h3>Quantidade:</td>
               <td align="right"><h3>Preco Unitário</td>
            </tr>
         </thead>
         <tbody>
""")
    for linha in app["lista"]:
        if linha[2]:
            arquivo.write("""
            <tr>
               <td>%s</td>
               <td>%s</td>
               <td align="right">%s</td>
               <td align="right">R$ %0.2f</td>
            </tr>
""" % tuple(linha))

    arquivo.write("""
         </tbody>
         <tfoot>
            <tr>
               <td colspan="4" align="right">Total: R$ %0.2f</td>
            </tr>
         </tfoot>
      </table>
   </center>
</body>
</html>
""" % total)
    arquivo.close()
    webbrowser.open_new("file://%s" % caminho)
# gera_relatorio()


def define_nome_relatorio(app, wid, nome_arquivo):
    app["nome_relatorio"] = nome_arquivo
# define_nome_relatorio()

app = App(title="Lista de Compras",
          help="Lista de compras para casa.",
          quit_callback=quit,
          statusbar=True,
          preferences=(Entry(id="nome_relatorio",
                             label="Nome do Arquivo",
                             value="relatorio.html"),
                       SaveFileButton(filter="text/html",
                                      callback=define_nome_relatorio)
                       ),
          top=(Button(id="gera_relatorio",
                      label="Gerar Lista de Compras",
                      callback=gera_relatorio),
               OpenFileButton(filter=["*.txt", "*.*"],
                              callback=escolhe_arquivo),
               Button(id="save", stock="save", callback=salva_arquivo),
               PreferencesButton(),
               ),
          center=(Label(id="nome_arquivo"),
                  Table(id="lista",
                        label="lista",
                        headers=("Categoria", "Descrição", "Quantidade",
                                 "Preco Unitário"),
                        types=(str, str, int, Decimal),
                        editable=True,
                        expand_columns_indexes=(0, 1),
                        data_changed_callback=dados_alterados,
                        ),
                  ),
          bottom=(Entry(id="total", label="Valor Total", editable=False),
                  ),
          )

define_nome_arquivo(app, None)
set_inactive("save", app)

run()
