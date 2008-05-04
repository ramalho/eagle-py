#!/usr/bin/env python
# -*- coding: utf-8 -*-

##servidor smtp: smtp.brturbo.com
##
##
##login: teste.python02
##senha: 123
##
##teste.python01@brturbo.com
##login: teste.python01
##senha: 123

from eagle import *
import smtplib

gNomeArquivo = None
mudancas = False
sb_ultimoID = []

def preencheTabela(table, nomeArquivo):
    del table[:] # limpa tabela

    # ler dados do arquivo
    arquivo = open(nomeArquivo, "r")
    for ln, linha in enumerate(arquivo):
        try:
            nome, email = linha.split(";")

            nome = nome.strip()
            email = email.strip()

            table.append((nome, email))
        except:
            error("Erro processando linha %d: %r" % (ln, linha))

    arquivo.close()
# preencheTabela()


def salvaTabela(table, nomeArquivo):
    arquivo = open(nomeArquivo, "w")
    for n, (nome, email) in enumerate(table):
        if not (nome and email):
            error("linha inválida %d pulada" %n)
            continue

        arquivo.write("%s;%s\n" %(nome, email))
    arquivo.close()
# salvaTabela()


def defineSemMudancas(app):
    for id in sb_ultimoID:
        app.remove_status_message(id)

    del sb_ultimoID[:]

    global mudancas
    mudancas = False
    set_inactive("save", app)
# defineSemMudancas()


def defineNomeArquivo(app, nomeArquivo=None):
    global gNomeArquivo

    if nomeArquivo:
        app["nomeArquivo"] = "Arquivo: %s" % nomeArquivo
        gNomeArquivo = nomeArquivo
    else:
        app["nomeArquivo"] = "Nenhum arquivo selecionado!"
        gNomeArquivo = None
# defineNomeArquivo()


def escolheArquivo(app, button, nomeArquivo):
    if mudancas:
        msg = "Ainda existem dados não salvos! Continuar e descartá-los?"
        if not yesno(msg):
            return

    defineNomeArquivo(app, nomeArquivo)
    if nomeArquivo:
        preencheTabela(app["contatos"], nomeArquivo)
        defineSemMudancas(app)
# escolheArquivo()


def dadosAlterados(app, table, data):
    global mudancas
    mudancas = True
    sb_ultimoID.append(app.status_message("Mudanças ainda não salvas!"))
    set_active("save", True, app)
# dadosAlterados()


def salvaArquivo(app, button):
    nomeArquivo = gNomeArquivo
    while nomeArquivo is None:
        nomeArquivo = app.file_chooser(FileChooser.ACTION_SAVE)

    defineNomeArquivo(app, nomeArquivo)

    salvaTabela(app["contatos"], gNomeArquivo)

    defineSemMudancas(app)
# salvaArquivo()


def quit(app):
    if mudancas:
        return yesno("Ainda existem dados não salvos!" \
                     "Continuar e descartá-los?")
    else:
        return True
# quit()


def enviaEmail(app, wid):
    msg = {}
    msg["From"] = app["email"]
    msg["To"] = app["Contato"]
    msg["Subject"] = app["Assunto"]
    msg["Mensagem"] = app["Mensagem"]
    serverSmtp = app["Smtp"]

    servidor = smtplib.SMTP() # Cria um objeto SMTP
    smtpserver = serverSmtp   # String com o nome do servidor

    servidor.connect(smtpserver, 25) #Conecta-se ao servidor
    servidor.login(app["Login"], app["Senha"])

    texto = """\
From: %(From)s\r
To: %(To)s\r
Subject: %(Subject)s\r
\r
%(Mensagem)s
""" % msg

    servidor.sendmail(msg['From'], msg['To'], texto)
    servidor.quit()
# enviaEmail()


def addContato(app, wid):
    selecionados = app["contatos"].selected()
    if not selecionados:
        return

    novos = []
    for indice, linha in selecionados:
        novos.append(linha)

    existentes = app["Contato"].replace("\n", ",").split(",")

    for existente in existentes:
        for i in xrange(len(novos)):
            if novos[i][1] in existente:
                del novos[i]
                break

    res = []
    for existente in existentes:
        existente = existente.strip()
        if existente:
            res.append(existente)

    for nome, email in novos:
        res.append("\"%s\" <%s>" % (nome, email))

    app["Contato"] = ",\n".join(res)
# addContato()


def delContato(app, wid):
    selecionados = app["contatos"].selected()
    if not selecionados:
        return

    novos = []
    for indice, linha in selecionados:
        novos.append(linha)

    existentes = app["Contato"].replace("\n", ",").split(",")

    res = []
    for existente in existentes:
        existente = existente.strip()
        if not existente:
            continue

        for i in xrange(len(novos)):
            if novos[i][1] in existente:
                break
        else:
            res.append(existente)

    app["Contato"] = ",\n".join(res)
# delContato()


app = App(title="Envia E-mails",
          author=("Caio",
                  "Alan"),
          help="Cliente simples para envio de e-mail.",
          quit_callback=quit,
          statusbar=True,
          top=(AboutButton(),
               QuitButton(),
               ),
          left=(Group(id="GroupContatos",
                      horizontal=True,
                      border=None,
                      children=(Group(id="GroupContatosTable",
                                      border=None,
                                      children=(Label(id="nomeArquivo"),
                                                Table(id="contatos",
                                                      label="Contatos",
                                                      editable=True,
                                                      headers=("Nome",
                                                               "Email"),
                                                      types=(str, str),
                                                      expand_columns_indexes=(0, 1),
                                                      data_changed_callback=dadosAlterados,
                                                      user_widgets=(OpenFileButton(callback=escolheArquivo),
                                                                    Button(id="save", stock="save",callback=salvaArquivo),

                                                                    ),
                                                      ),
                                                ),
                                      ),
                                Group(id="GroupAcoesContatos",
                                      border=None,
                                      expand_policy=ExpandPolicy.Nothing(),
                                      children=(Button(id="add",
                                                       label=">>",
                                                       callback=addContato),
                                                Button(id="del",
                                                       label="<<",
                                                       callback=delContato),
                                                ),
                                      ),
                                )
                      ),
                ),
          right=(Entry(id="Smtp",
                       label="Seu servidor Smtp:",
                       persistent=True),
                 Entry(id="Email"
                       ,label="Seu Email:",
                       persistent=True),
                 Entry(id="Login",
                       label="Seu login:",
                       persistent=True),
                 Entry(id="Senha",
                       label="Sua Senha:",
                       persistent=True),
                 Entry(id="Contato",
                       label="Enviar Para:",
                       multiline=True,
                       persistent=True),
                 Entry(id="Assunto",
                       label="Assunto:",
                       persistent=True),
                 Entry(id="Mensagem",
                       label="Mensagem:",
                       multiline=True,
                       persistent=True),
                Button(id="Enviar",
                       label="Enviar",
                       callback=enviaEmail),
                 ),
          )

defineNomeArquivo(app, None)
set_inactive("save", app)

run()
