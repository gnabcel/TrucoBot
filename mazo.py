#!/usr/bin/env python3
from envido import contarEnvido

# Truco .
# Language: Python 3#

# Definimos un diccionario para asociar cada número de carta con su nombre
nombres_cartas = {1: 'Ancho de espada', 2: 'Ancho de basto', 3: 'Siete de espada', 4: 'Siete de oro',
                  5: 'Tres de espada', 6: 'Tres de oro', 7: 'Tres de copa', 8: 'Tres de basto',
                  9: 'Dos de espada', 10: 'Dos de basto', 11: 'Dos de oro', 12: 'Dos de espada',
                  13: 'Ancho de copa', 14: 'Ancho de oro',
                  15: 'Rey de espada', 16: 'Rey de basto', 17: 'Rey de oro', 18: 'Rey de copa',
                  19: 'Caballo de espada', 20: 'Caballo de basto', 21: 'Caballo de oro', 22: 'Caballo de copa',
                  23: 'Sota de espada', 24: 'Sota de basto', 25: 'Sota de oro', 26: 'Sota de copa',
                  27: 'Siete de copa', 28: 'Siete de basto',
                  29: 'Seis de espada', 30: 'Seis de basto', 31: 'Seis de oro', 32: 'Seis de copa',
                  33: 'Cinco de espada', 34: 'Cinco de basto', 35: 'Cinco de oro', 36: 'Cinco de copa',
                  37: 'Cuatro de espada', 38: 'Cuatro de basto', 39: 'Cuatro de oro', 40: 'Cuatro de copa'}

cartas_valor = {
    "1e": 30, "1b": 29, "7e": 28, "7o": 27,
    "3e": 26, "3b": 26, "3c": 26, "3o": 26,
    "2e": 22, "2b": 22, "2c": 22, "2o": 22,
    "1c": 21, "1o": 21,
    "12e": 9, "12b": 9, "12c": 9, "12o": 9,
    "11e": 8, "11b": 8, "11c": 8, "11o": 8,
    "10e": 6, "10b": 6, "10c": 6, "10o": 6,
    "7c": 5, "7b": 5,
    "6e": 3, "6b": 3, "6c": 3, "6o": 3,
    "5e": 2, "5b": 2, "5c": 2, "5o": 2,
    "4e": 1, "4b": 1, "4c": 1, "4o": 1,
}

import random
import colored


# Creamos una función para mezclar el mazo
def mezclar_mazo():
    global mazo
    mazo = []
    for key in cartas_valor.keys():
        mazo.append(key)
    return random.shuffle(mazo)


# Mezclamos el mazo y lo asignamos a una variable
mezclar_mazo()

# Creamos una lista vacía para cada mano de jugador
manoA = [mazo[0], mazo[1], mazo[2]]
manoB = [mazo[3], mazo[4], mazo[5]]


# Definimos una función para evaluar una jugada
def evaluar_ganador_de_ronda(A, B, ronda_n=None):
    if cartas_valor[A] == cartas_valor[B] and ronda_n == 1:
        return 'parda'
    if cartas_valor[A] == cartas_valor[B]:
        return 'empate, pero no parda'
    if cartas_valor[A] > cartas_valor[B]:
        return 'jugardor 1 gana con ' + A
    else:
        return 'jugardor 2 gana con ' + B


# Definimos una función para jugar una ronda
def jugar_ronda(manoA, manoB, ronda):
    print(evaluar_ganador_de_ronda(manoA[ronda], manoB[ronda]))


def rondas():
    for i in range(3):
        print("Ronda numero:", i + 1)
        jugar_ronda(manoA, manoB, i)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print('--------------------------------------')
    print('Mano jugador 1: ' + str(manoA))
    print('Mano jugador 2: ' + str(manoB))
    print('--------------------------------------')
    rondas()
    print('--------------------------------------')
    print('jugador 1 envido: ' + contarEnvido(manoA[0], manoA[1], manoA[2]))
    print('jugador 2 envido: ' + contarEnvido(manoB[0], manoB[1], manoB[2]))
