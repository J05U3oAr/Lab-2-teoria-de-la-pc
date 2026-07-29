import sys

PAREJAS = {')': '(', ']': '[', '}': '{'}
APERTURAS = set(PAREJAS.values())
CIERRES = set(PAREJAS.keys())


def formato_pila(pila):
    return '[' + ' '.join(pila) + ']' if pila else '[vacia]'


def verificar_balance(expresion):
    pila = []
    pasos = []

    for i, char in enumerate(expresion):
        if char in APERTURAS:
            pila.append(char)
            pasos.append(f"  pos {i:>3} | '{char}' -> PUSH        | pila: {formato_pila(pila)}")

        elif char in CIERRES:
            if not pila:
                pasos.append(f"  pos {i:>3} | '{char}' -> ERROR: no hay simbolo abierto que cerrar | pila: {formato_pila(pila)}")
                return False, pasos

            tope = pila.pop()
            if tope != PAREJAS[char]:
                pasos.append(f"  pos {i:>3} | '{char}' -> ERROR: se esperaba cierre de '{tope}', no coincide | pila: {formato_pila(pila)}")
                return False, pasos

            pasos.append(f"  pos {i:>3} | '{char}' -> POP '{tope}' (coincide) | pila: {formato_pila(pila)}")

    if pila:
        pasos.append(f"  Fin de linea -> ERROR: quedaron simbolos sin cerrar en la pila: {formato_pila(pila)}")
        return False, pasos

    pasos.append("  Fin de linea -> pila vacia, expresion balanceada")
    return True, pasos


def procesar_archivo(ruta):
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            lineas = [linea.rstrip('\n') for linea in f]
    except FileNotFoundError:
        print(f"Error: no se encontro el archivo '{ruta}'")
        sys.exit(1)

    total = 0
    balanceadas = 0

    for num_linea, expresion in enumerate(lineas, start=1):
        if expresion.strip() == '':
            continue

        total += 1
        print("=" * 70)
        print(f"Linea {num_linea}: {expresion}")
        print("-" * 70)

        resultado, pasos = verificar_balance(expresion)
        for paso in pasos:
            print(paso)

        estado = "BALANCEADA" if resultado else "NO BALANCEADA"
        print(f"\n  >> Resultado: {estado}")
        print()

        if resultado:
            balanceadas += 1

    print("=" * 70)
    print(f"Resumen: {balanceadas}/{total} expresiones balanceadas")


if __name__ == "__main__":
    archivo = sys.argv[1] if len(sys.argv) > 1 else "expresiones.txt"
    print(f"Procesando archivo: {archivo}\n")
    procesar_archivo(archivo)