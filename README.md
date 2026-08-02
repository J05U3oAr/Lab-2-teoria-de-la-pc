# Lab 2

Este repositorio contiene los archivos trabajados para el laboratorio. La idea general es probar dos cosas: primero, revisar si una expresion tiene sus simbolos balanceados; segundo, convertir expresiones regulares a formato postfix usando el algoritmo Shunting Yard.

## Demostracion

Video con la demostracion de la funcionalidad de ambos ejercicios:

https://youtu.be/SlQIlYCBJtg

## Carpetas y archivos

### `.git/`

Carpeta interna de Git. Guarda el historial del repositorio y la informacion necesaria para controlar versiones del proyecto.

### `Ejercicio_2/`

Carpeta del segundo ejercicio. Aqui esta el programa que revisa si los parentesis, corchetes y llaves de cada expresion estan correctamente balanceados.

- `Ejercicio2.py`: script principal del ejercicio 2. Lee expresiones desde un archivo `.txt`, usa una pila para validar aperturas y cierres, muestra los pasos realizados y al final imprime un resumen.
- `expresiones.txt`: archivo de entrada con las expresiones que se prueban en el ejercicio 2.

### `Ejercicio_3/`

Carpeta del tercer ejercicio. Aqui esta el programa que convierte expresiones regulares de notacion infija a notacion postfix.

- `Ejercicio3.py`: script principal del ejercicio 3. Tokeniza las expresiones, agrega concatenaciones explicitas, valida la sintaxis, aplica Shunting Yard y convierte extensiones como `+`, `?` y `{m,n}` a operaciones basicas.
- `explicacion_shunting_yard.txt`: texto corto que explica como funciona el algoritmo Shunting Yard y como se adapta para las expresiones regulares del ejercicio.
- `expresiones.txt`: archivo de entrada con expresiones regulares usadas para probar la conversion a postfix.

### `Ejercicio_3/__pycache__/`

Carpeta generada automaticamente por Python. No es parte principal del codigo, solo guarda archivos compilados para que Python pueda cargar el programa mas rapido.

- `Ejercicio3.cpython-313.pyc`: version compilada automaticamente de `Ejercicio3.py`.
