#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from eagle import *
import random
import os

globo = []

# faz a roleta girar, utilizando o método random
def giraRoleta(app, button):
    if not globo:
        error("Acabaram-se os números!")
        return

    random.shuffle(globo)  # embaralha lista "globo"
    sorteado = globo.pop() # retira o último número da lista

    app["numeroSorteado"] = sorteado # mostra número sorteado
    app["numerosSorteados"].insert(0, sorteado) # adiciona na tabela de sorteados


def iniciaJogo(app, wid=None, valor=0):
    tabela = app["numerosSorteados"]
    del tabela[:] # limpa tabela de sorteados

    app["numeroSorteado"] = "" # limpa campo numero sorteado

    inicio = app["seqInicio"]
    fim = app["seqFim"]

    global globo
    globo = range(inicio, fim + 1)



app = App(title="Heleno & Jean's Bingo",
          help="Programa para sorteio de numeros para Bingos.",
          author=("Heleno da Maia",
                  "Jean Carlos de Souza"),
          window_size=(300, 300),
          top=(Button(id="novoJogo",
                      stock="new",
                      callback=iniciaJogo),
               Button(id="giraRoleta",
                      label="Girar a Roleta",
                      callback=giraRoleta),
               AboutButton(),
               QuitButton(),

               ),
          left=(UIntSpin(id="seqInicio",
                         label="Início:",
                         value=1,
                         min=1,
                         max=100,
                         step=1,
                         persistent=True,
                         callback=iniciaJogo),
                UIntSpin(id="seqFim",
                         label="Fim: ",
                         value=100,
                         min=1,
                         max=100,
                         step=1,
                         persistent=True,
                         callback=iniciaJogo),
                ),
          center=(Entry(id="numeroSorteado",
                        label="Número Sorteado:",
                        editable=False),
                  ),
          right=(Table(id="numerosSorteados",
                       label="Números Sorteados",
                       headers=None,
                       types=(int,),
                       show_headers=False,
                       ),
                 ),
          )

iniciaJogo(app)
run()
