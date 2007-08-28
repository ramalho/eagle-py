#!/usr/bin/env python
#-*- coding: utf-8 -*-

from eagle import *

def formata_ip(ip):
    return ".".join(str((ip >> (8 * (3 - n))) & 0xff) for n in xrange(4))

def calcular(app, *a):
    endereco_ip = [app["IP1"], app["IP2"], app["IP3"], app["IP4"]]
    ip = sum((v << (8 * (3 - n))) for n, v in enumerate(endereco_ip))

    if 1 <= endereco_ip[0] <= 127:
        classe = "A"
        mascara = 0xff000000
    elif 128 <= endereco_ip[0] <= 191:
        classe = "B"
        mascara = 0xffff0000
    elif 191 <= endereco_ip[0] <= 224:
        classe = "C"
        mascara = 0xffffff00
    else:
        classe = "Erro"
        mascara = 0xffffffff

    neg_mascara = ~mascara
    n_hosts = 0xffffffff & neg_mascara - 1

    subrede = ip & mascara
    broadcast = subrede | neg_mascara
    primeiro = formata_ip(subrede + 1)
    ultimo = formata_ip(broadcast - 1)

    subrede = formata_ip(subrede)
    broadcast = formata_ip(broadcast)
    mascara = formata_ip(mascara)

    if classe == "Erro":
        app["classe"] = "IP Invalido"
        app["mascara"] = ''
        app["quantidade_de_host"] = ''
        app["subrede"] = ''
        app["primeiro"] = ''
        app["ultimo"] = ''
        app["broadcast"] = ''
    else:
        app["classe"] = '1) Classe: %s' % classe
        app["mascara"] = '2) Mascara Padrão: %s' % mascara
        app["n_hosts"] = '3) Quantidade De Hosts: %d' % n_hosts
        app["subrede"] = '4) Endereço De SubRede: %s' % subrede
        app["primeiro"] = '5) Primeiro Endereço IP Válido: %s' % primeiro
        app["ultimo"] = '6) Ultimo Endereço IP Válido: %s' % ultimo
        app["broadcast"] = '7) Endereço De BroadCast: %s' % broadcast

App(title="Calculadora IP",
    window_size=(450, 450),
    top=(HelpButton(), AboutButton(), QuitButton()),
    author=("André Tesck (razak.ss@gmail.com)",
            "Dionisio Patrick (patricksant@gmail.com)"),
    version="Beta",
    license="Eagle",
    description="""\
Calculadora De IP desenvolvida para trabalho de programação ministrado
pelo Marco André.""",
    help="""\
No campo <b>Número de IP</b> insira o endereço de IP válido e então
pressione o botão <b>Calcular</b> localizado na parte inferior do
programa.""",
    center=(Group(id="grpIP", label="Endereço IP:", horizontal=True,
                  children=(UIntSpin(id="IP1", label=None,
                                     value=192, min=1, max=255, step=1,
                                     persistent=True, callback=calcular),
                            UIntSpin(id="IP2", label=None,
                                     value=168, min=0, max=255, step=1,
                                     persistent=True, callback=calcular),
                            UIntSpin(id="IP3", label=None,
                                     value=0, min=0, max=255, step=1,
                                     persistent=True, callback=calcular),
                            UIntSpin(id="IP4", label=None,
                                     value=1, min=0, max=255, step=1,
                                     persistent=True, callback=calcular),
                            ),
                  ),
            Group(id="grpSaida", label="Informações:",
                  children=(Label(id="classe",
                                  expand_policy=ExpandPolicy.Horizontal()),
                            Label(id="mascara",
                                  expand_policy=ExpandPolicy.Horizontal()),
                            Label(id="n_hosts",
                                  expand_policy=ExpandPolicy.Horizontal()),
                            Label(id="subrede",
                                  expand_policy=ExpandPolicy.Horizontal()),
                            Label(id="primeiro",
                                  expand_policy=ExpandPolicy.Horizontal()),
                            Label(id="ultimo",
                                  expand_policy=ExpandPolicy.Horizontal()),
                            Label(id="broadcast",
                                  expand_policy=ExpandPolicy.Horizontal()),
                            ),
                  expand_policy=ExpandPolicy.All(),
                  ),
            ),
    bottom=(Button(id="calcular", label="Calcular", callback=calcular))
    )

run()
