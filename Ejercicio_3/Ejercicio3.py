import copy
import sys
from dataclasses import dataclass


EPSILON = "epsilon"
CONCAT = "CONCAT"


@dataclass(frozen=True)
class Token:
    tipo: str
    valor: object
    texto: str
    posicion: int


@dataclass(frozen=True)
class Nodo:
    tipo: str
    valor: object = None
    hijos: tuple = ()


PRECEDENCIA = {
    "|": 1,
    CONCAT: 2,
}


def es_operador_binario(token):
    return token.tipo in {"UNION", "CONCAT"}


def puede_terminar_operando(token):
    return token.tipo in {"LITERAL", "CLASE", "RPAREN", "STAR", "PLUS", "QUESTION", "REPEAT"}


def puede_iniciar_operando(token):
    return token.tipo in {"LITERAL", "CLASE", "LPAREN"}


def formato_tokens(tokens):
    return " ".join(token.texto for token in tokens) if tokens else "(vacio)"


def escapar_literal(char):
    especiales = {"\\", "|", "*", "+", "?", "(", ")", "[", "]", "{", "}", " "}
    return "\\" + char if char in especiales else char


def leer_clase(expresion, inicio):
    profundidad = 0
    i = inicio
    while i < len(expresion):
        char = expresion[i]
        if char == "\\":
            if i + 1 >= len(expresion):
                raise ValueError(f"Caracter de escape incompleto dentro de clase en posicion {i}")
            i += 2
            continue
        if char == "[":
            profundidad += 1
        elif char == "]":
            profundidad -= 1
            if profundidad == 0:
                return expresion[inicio : i + 1], i + 1
        i += 1
    raise ValueError(f"Clase de caracteres sin cierre desde posicion {inicio}")


def leer_repeticion(expresion, inicio):
    fin = expresion.find("}", inicio + 1)
    if fin == -1:
        raise ValueError(f"Repeticion sin cierre desde posicion {inicio}")

    contenido = expresion[inicio + 1 : fin].replace(" ", "")
    if not contenido:
        raise ValueError(f"Repeticion vacia en posicion {inicio}")

    if "," in contenido:
        partes = contenido.split(",")
        if len(partes) != 2:
            raise ValueError(f"Repeticion invalida en posicion {inicio}: {{{contenido}}}")
        minimo_txt, maximo_txt = partes
        if minimo_txt == "":
            raise ValueError(f"La repeticion debe tener minimo en posicion {inicio}")
        if not minimo_txt.isdigit() or (maximo_txt and not maximo_txt.isdigit()):
            raise ValueError(f"Repeticion invalida en posicion {inicio}: {{{contenido}}}")
        minimo = int(minimo_txt)
        maximo = int(maximo_txt) if maximo_txt else None
    else:
        if not contenido.isdigit():
            raise ValueError(f"Repeticion invalida en posicion {inicio}: {{{contenido}}}")
        minimo = int(contenido)
        maximo = minimo

    if maximo is not None and minimo > maximo:
        raise ValueError(f"Repeticion invalida en posicion {inicio}: minimo mayor que maximo")

    return (minimo, maximo), expresion[inicio : fin + 1], fin + 1


def tokenizar(expresion):
    tokens = []
    pasos = []
    i = 0

    while i < len(expresion):
        char = expresion[i]

        if char.isspace():
            i += 1
            continue

        if char == "\\":
            if i + 1 >= len(expresion):
                raise ValueError(f"Caracter de escape incompleto en posicion {i}")
            literal = expresion[i + 1]
            token = Token("LITERAL", literal, escapar_literal(literal), i)
            tokens.append(token)
            pasos.append(f"pos {i}: '\\{literal}' se toma como literal escapado")
            i += 2
            continue

        if char == "[":
            texto, nuevo_i = leer_clase(expresion, i)
            tokens.append(Token("CLASE", texto, texto, i))
            pasos.append(f"pos {i}: clase de caracteres {texto} se toma como operando")
            i = nuevo_i
            continue

        if char == "{":
            repeticion, texto, nuevo_i = leer_repeticion(expresion, i)
            tokens.append(Token("REPEAT", repeticion, texto, i))
            pasos.append(f"pos {i}: extension {texto} validada como repeticion")
            i = nuevo_i
            continue

        if char == "^":
            j = i + 1
            while j < len(expresion) and expresion[j].isspace():
                j += 1
            if j < len(expresion) and expresion[j] == "{":
                pasos.append(f"pos {i}: '^' se reconoce como marcador de repeticion")
                i += 1
                continue

        if char == "(":
            tokens.append(Token("LPAREN", char, char, i))
        elif char == ")":
            tokens.append(Token("RPAREN", char, char, i))
        elif char == "|":
            tokens.append(Token("UNION", char, char, i))
        elif char == "*":
            tokens.append(Token("STAR", char, char, i))
        elif char == "+":
            tokens.append(Token("PLUS", char, char, i))
        elif char == "?":
            tokens.append(Token("QUESTION", char, char, i))
        elif char in {"]", "}"}:
            raise ValueError(f"Caracter de cierre inesperado '{char}' en posicion {i}")
        else:
            tokens.append(Token("LITERAL", char, escapar_literal(char), i))

        i += 1

    return tokens, pasos


def insertar_concatenacion(tokens):
    resultado = []
    pasos = []

    for token in tokens:
        if resultado and puede_terminar_operando(resultado[-1]) and puede_iniciar_operando(token):
            concat = Token("CONCAT", CONCAT, CONCAT, token.posicion)
            resultado.append(concat)
            pasos.append(
                f"antes de pos {token.posicion}: se inserta {CONCAT} entre "
                f"'{resultado[-2].texto}' y '{token.texto}'"
            )
        resultado.append(token)

    return resultado, pasos


def validar_sintaxis(tokens):
    espera_operando = True
    balance = 0

    for token in tokens:
        if token.tipo in {"LITERAL", "CLASE"}:
            if not espera_operando:
                raise ValueError(f"Falta operador antes de '{token.texto}' en posicion {token.posicion}")
            espera_operando = False
        elif token.tipo == "LPAREN":
            if not espera_operando:
                raise ValueError(f"Falta operador antes de '(' en posicion {token.posicion}")
            balance += 1
            espera_operando = True
        elif token.tipo == "RPAREN":
            if espera_operando:
                raise ValueError(f"Grupo vacio o operador incompleto antes de ')' en posicion {token.posicion}")
            balance -= 1
            if balance < 0:
                raise ValueError(f"Parentesis de cierre sin apertura en posicion {token.posicion}")
            espera_operando = False
        elif token.tipo in {"STAR", "PLUS", "QUESTION", "REPEAT"}:
            if espera_operando:
                raise ValueError(f"Extension '{token.texto}' sin operando en posicion {token.posicion}")
            espera_operando = False
        elif es_operador_binario(token):
            if espera_operando:
                raise ValueError(f"Operador '{token.texto}' sin operando izquierdo en posicion {token.posicion}")
            espera_operando = True

    if balance > 0:
        raise ValueError("Hay parentesis de apertura sin cerrar")
    if espera_operando and tokens:
        raise ValueError("La expresion termina con un operador incompleto")


def a_postfix(tokens):
    salida = []
    pila = []
    pasos = []

    for token in tokens:
        if token.tipo in {"LITERAL", "CLASE"}:
            salida.append(token)
            pasos.append(f"leer {token.texto}: va a salida -> {formato_tokens(salida)}")
        elif token.tipo in {"STAR", "PLUS", "QUESTION", "REPEAT"}:
            salida.append(token)
            pasos.append(f"leer {token.texto}: operador postfix, va a salida -> {formato_tokens(salida)}")
        elif token.tipo == "LPAREN":
            pila.append(token)
            pasos.append(f"leer (: push en pila -> {formato_tokens(pila)}")
        elif token.tipo == "RPAREN":
            pasos.append("leer ): desapilar hasta encontrar (")
            while pila and pila[-1].tipo != "LPAREN":
                salida.append(pila.pop())
                pasos.append(f"  pop a salida -> {formato_tokens(salida)}")
            if not pila:
                raise ValueError("Parentesis desbalanceados durante Shunting Yard")
            pila.pop()
            pasos.append(f"  se descarta ( -> pila {formato_tokens(pila)}")
        elif es_operador_binario(token):
            while (
                pila
                and es_operador_binario(pila[-1])
                and PRECEDENCIA[pila[-1].valor] >= PRECEDENCIA[token.valor]
            ):
                salida.append(pila.pop())
                pasos.append(f"leer {token.texto}: pop por precedencia -> {formato_tokens(salida)}")
            pila.append(token)
            pasos.append(f"leer {token.texto}: push en pila -> {formato_tokens(pila)}")

    while pila:
        if pila[-1].tipo == "LPAREN":
            raise ValueError("Parentesis de apertura sin cierre durante Shunting Yard")
        salida.append(pila.pop())
        pasos.append(f"fin: pop restante -> {formato_tokens(salida)}")

    return salida, pasos


def construir_ast(postfix):
    pila = []

    for token in postfix:
        if token.tipo in {"LITERAL", "CLASE"}:
            pila.append(Nodo(token.tipo, token.texto))
        elif token.tipo == "STAR":
            pila.append(Nodo("STAR", hijos=(pila.pop(),)))
        elif token.tipo == "PLUS":
            pila.append(Nodo("PLUS", hijos=(pila.pop(),)))
        elif token.tipo == "QUESTION":
            pila.append(Nodo("QUESTION", hijos=(pila.pop(),)))
        elif token.tipo == "REPEAT":
            pila.append(Nodo("REPEAT", token.valor, (pila.pop(),)))
        elif token.tipo == "CONCAT":
            derecho = pila.pop()
            izquierdo = pila.pop()
            pila.append(Nodo("CONCAT", hijos=(izquierdo, derecho)))
        elif token.tipo == "UNION":
            derecho = pila.pop()
            izquierdo = pila.pop()
            pila.append(Nodo("UNION", hijos=(izquierdo, derecho)))

    if len(pila) != 1:
        raise ValueError("No se pudo construir un arbol valido desde el postfix")
    return pila[0]


def concatenar(nodos):
    if not nodos:
        return Nodo("EPSILON")
    actual = nodos[0]
    for nodo in nodos[1:]:
        actual = Nodo("CONCAT", hijos=(actual, nodo))
    return actual


def expandir_extensiones(nodo):
    if nodo.tipo in {"LITERAL", "CLASE", "EPSILON"}:
        return nodo
    if nodo.tipo == "STAR":
        return Nodo("STAR", hijos=(expandir_extensiones(nodo.hijos[0]),))
    if nodo.tipo == "CONCAT":
        return Nodo("CONCAT", hijos=(expandir_extensiones(nodo.hijos[0]), expandir_extensiones(nodo.hijos[1])))
    if nodo.tipo == "UNION":
        return Nodo("UNION", hijos=(expandir_extensiones(nodo.hijos[0]), expandir_extensiones(nodo.hijos[1])))
    if nodo.tipo == "PLUS":
        base = expandir_extensiones(nodo.hijos[0])
        return Nodo("CONCAT", hijos=(copy.deepcopy(base), Nodo("STAR", hijos=(copy.deepcopy(base),))))
    if nodo.tipo == "QUESTION":
        base = expandir_extensiones(nodo.hijos[0])
        return Nodo("UNION", hijos=(base, Nodo("EPSILON")))
    if nodo.tipo == "REPEAT":
        minimo, maximo = nodo.valor
        base = expandir_extensiones(nodo.hijos[0])
        partes = [copy.deepcopy(base) for _ in range(minimo)]
        if maximo is None:
            partes.append(Nodo("STAR", hijos=(copy.deepcopy(base),)))
        else:
            for _ in range(maximo - minimo):
                partes.append(Nodo("UNION", hijos=(copy.deepcopy(base), Nodo("EPSILON"))))
        return concatenar(partes)
    raise ValueError(f"Tipo de nodo no reconocido: {nodo.tipo}")


def ast_a_postfix(nodo):
    if nodo.tipo == "LITERAL":
        return [nodo.valor]
    if nodo.tipo == "CLASE":
        return [nodo.valor]
    if nodo.tipo == "EPSILON":
        return [EPSILON]
    if nodo.tipo == "STAR":
        return ast_a_postfix(nodo.hijos[0]) + ["*"]
    if nodo.tipo == "CONCAT":
        return ast_a_postfix(nodo.hijos[0]) + ast_a_postfix(nodo.hijos[1]) + [CONCAT]
    if nodo.tipo == "UNION":
        return ast_a_postfix(nodo.hijos[0]) + ast_a_postfix(nodo.hijos[1]) + ["|"]
    raise ValueError(f"No se puede imprimir nodo extendido sin convertir: {nodo.tipo}")


def convertir_expresion(expresion):
    tokens, pasos_token = tokenizar(expresion)
    tokens_con_concat, pasos_concat = insertar_concatenacion(tokens)
    validar_sintaxis(tokens_con_concat)
    postfix_extendido, pasos_shunting = a_postfix(tokens_con_concat)
    ast_extendido = construir_ast(postfix_extendido)
    ast_basico = expandir_extensiones(ast_extendido)
    postfix_final = ast_a_postfix(ast_basico)

    pasos = []
    pasos.extend(pasos_token)
    pasos.extend(pasos_concat)
    pasos.append(f"tokens con concatenacion explicita: {formato_tokens(tokens_con_concat)}")
    pasos.extend(pasos_shunting)
    pasos.append(f"postfix extendido: {formato_tokens(postfix_extendido)}")
    pasos.append("se convierten extensiones: A+ = A A * CONCAT, A? = A epsilon |, A{m,n} = repeticiones/optionales")
    pasos.append(f"postfix final: {' '.join(postfix_final)}")

    return postfix_final, pasos


def procesar_archivo(ruta):
    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            lineas = [linea.rstrip("\n") for linea in archivo]
    except FileNotFoundError:
        print(f"Error: no se encontro el archivo '{ruta}'")
        sys.exit(1)

    procesadas = 0
    correctas = 0

    for numero, expresion in enumerate(lineas, start=1):
        if expresion.strip() == "":
            continue

        procesadas += 1
        print("=" * 80)
        print(f"Linea {numero}: {expresion}")
        print("-" * 80)

        try:
            postfix, pasos = convertir_expresion(expresion)
            print("(a) Expresion en formato postfix:")
            print(" ".join(postfix))
            print("\n(b) Pasos realizados:")
            for paso in pasos:
                print(f"  - {paso}")
            correctas += 1
        except ValueError as error:
            print("(a) Expresion en formato postfix:")
            print("No se pudo convertir la expresion.")
            print("\n(b) Pasos realizados:")
            print(f"  - ERROR: {error}")
        print()

    print("=" * 80)
    print(f"Resumen: {correctas}/{procesadas} expresiones convertidas correctamente")


if __name__ == "__main__":
    archivo_entrada = sys.argv[1] if len(sys.argv) > 1 else "expresiones.txt"
    print(f"Procesando archivo: {archivo_entrada}\n")
    procesar_archivo(archivo_entrada)
