import re
import toml

from .config import load_config
from collections import deque

assign_last_value = True
lista_regex = deque(maxlen=3)
regras_globais = None

def carregar_regras():
    global regras_globais
    
    if regras_globais is None: 
        config = load_config()
        regex_caminho = config["caminho_regex"]
        #print(regex_caminho)
        #with open(r'D:\quattroD\Produção quattroD - General\DYNAMO\DYNAMO - Revisados 2024\Teste-AW\aw-watcher-quattrod.toml', "r") as f:
        regras_regex = toml.load(regex_caminho)
        regras_globais = regras_regex["regex"]
        #print(regras_globais)

    #print(f"TOML: {regras_globais}")
    return regras_globais

def aplicar_regex(texto, regras):
    global assign_last_value
    resultados = []

    for regra in regras:
        nome = regra["nome"]
        padrao = regra["padrao"]
        correspondencias = re.findall(padrao, texto)
        if correspondencias:
            assign_last_value = True
            return nome  # Retorna o primeiro regex encontrado

    if assign_last_value and lista_regex:
        assign_last_value = False
        last_value = lista_regex[-1]
        if last_value:
            return f"{last_value} (***)"
        else:
            return "Regex não encontrado"
    elif lista_regex:
        return lista_regex[-1]
    else:
        return "Regex não encontrado"

def regex(texto):
    regras = carregar_regras()
    regex_result = aplicar_regex(texto, regras)
    #print(f"Título: {texto}, Resultado: {regex_result}")
    lista_regex.append(regex_result)
    #print(f"Lista: {teste}")
    return regex_result
