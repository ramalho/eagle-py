#!/usr/bin/env python
#-*- coding: utf-8 -*-
from eagle import *
import random

lista1 = ['carro',
          'papai',
          'letra',
          'meses',
          'velha',
          'linux',
          'anual',
          'grupo',
          'tenda',
          'mundo',
          'lapis',
          'predio',
          'oculos',
          'dente',
          'olho',
          'malhar',
          'clipe',
          'filtro',
          'video',
          'entrar',
          'bolsa',
          'filme',
          'dados']
lista2 = ['memoria',
          'roberto',
          'messias',
          'cortina',
          'noticia',
          'aplicar',
          'navegar',
          'palavra',
          'mostrar',
          'amarelo',
          'tornear',
          'empresa',
          'pesquisa',
          'perola',
          'monitorar',
          'penetrar',
          'mochila',
          'capacete',
          'encontro',
          'pipoca',
          'pesquisa',
          'familiar',
          'rotina']
lista3 = ['tecnologia',
          'industrial',
          'programas',
          'impressora',
          'deficiente',
          'objetivo',
          'armazenamento',
          'anagrama',
          'servidor',
          'consultoria',
          'anfiteatro',
          'estacionamento',
          'auditorio',
          'dificuldade',
          'atualizar',
          'software',
          'atenciosamente',
          'computador',
          'algoritmo',
          'dicionario']

anagrama = ""
palavra = ""

def iniciarJogo(app, wid, valor=None):
    global anagrama, palavra

    nivel = app["nivel"]
    if nivel == "Iniciante":
        listaPalavras = lista1
    elif nivel == "Intermediario":
        listaPalavras = lista2
    else:
        listaPalavras = lista3

    palavra = random.choice(listaPalavras)  #escolhe uma palavra da lista
    palavraLista = list(palavra)            #transforma uma string em uma lista
    random.shuffle(palavraLista)            #embaralha letras na lista
    anagrama = "".join(palavraLista)        #palavra embaralhada em uma string
    app["anagrama"] = anagrama
    app["nrTentativas"] = 100
    app["mensagem"] = ""
    app["tentativa"] = ""


def submeterResposta(app, wid):
    #Pega valores da tela
    tentativa = app["tentativa"]
    #analisa
    if tentativa == palavra:
        app["mensagem"] = "Parabéns, voce conseguiu!!"
    else:
        app["mensagem"] = "Voce não conseguiu, Tente outra vez!"
        #atualiza barra de progresso
        tentativas = float(app["nrTentativas"])
        tentativas = (int(tentativas * 10) - 2) / 10.0
        if tentativas >= 0:
            app["nrTentativas"] = tentativas
        else:
            return

        if tentativas == 0:
            app["mensagem"] = "Você perdeu! A palavra era: %s." %palavra

App(title="Anagrama",
    author="Luis Fernando Machado - luissimm@gmail.com",
    version="1.1",
    license="GNU LGPL",
    description="Jogo de anagramas.",
    window_size = (500, 350),
    top=(Button(id="novo", stock="new", callback=iniciarJogo),
         HelpButton(),
         AboutButton(),
         QuitButton(),
         ),
    center=(Group(id="groupAnagrama",
                  label=None,
                  children=(Selection(id="nivel",
                                      label="Nivel:",
                                      options=("Iniciante",
                                               "Intermediário",
                                               "Avancado"),
                                      active="Iniciante",
                                      persistent=True,
                                      callback=iniciarJogo),
                            Entry(id="anagrama",
                                  label="Anagrama:",
                                  editable=False),
                            ),
                  ),
            Group(id="groupResposta",
                  label=None,
                  #horizontal=True,
                  children=(Entry(id="tentativa",
                                  label="Palavra:"),
                            Button(id="bSubmeter",
                                   label="Ok",
                                   callback=submeterResposta),
                            ),
                  ),
            Group(id="Mensagem",
                  label=None,
                  children=(Progress(id="nrTentativas",
                                     label="Tentativas",
                                     value=1),
                            Entry(id="mensagem",
                                  label="Mensagem:",
                                  editable=False),
                            ),
                  ),
            ),
    )

run()
