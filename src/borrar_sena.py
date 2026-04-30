import argparse

import pandas as pd

from config import DATASET_PATH, ENTRADA_MODELO, LEGACY_DATASET_PATH
from vocabulario_lsc import normalizar_etiqueta


def cargar_dataset():
    dataset = DATASET_PATH if DATASET_PATH.exists() else LEGACY_DATASET_PATH
    if not dataset.exists():
        return dataset, None

    columnas = ["sena"] + [f"p{i}" for i in range(ENTRADA_MODELO)]
    datos = pd.read_csv(dataset, header=None, names=columnas, usecols=range(ENTRADA_MODELO + 1))
    return dataset, datos


def listar_senas(datos):
    resumen = datos["sena"].value_counts().sort_values(ascending=False)
    print("\nSenas disponibles:")
    print(resumen.to_string())


def borrar_sena(nombre_sena, confirmar=False):
    dataset, datos = cargar_dataset()

    if datos is None:
        print("Todavia no existe el dataset.")
        return

    etiqueta = normalizar_etiqueta(nombre_sena)
    coincidencias = datos["sena"] == etiqueta
    total = int(coincidencias.sum())

    if total == 0:
        print(f"No se encontro la sena '{etiqueta}'.")
        listar_senas(datos)
        return

    print(f"Se eliminaran {total} muestras de la sena '{etiqueta}'.")

    if not confirmar:
        respuesta = input("Escriba SI para confirmar: ").strip().upper()
        if respuesta != "SI":
            print("Operacion cancelada.")
            return

    datos_filtrados = datos.loc[~coincidencias]
    datos_filtrados.to_csv(dataset, header=False, index=False)
    print(f"Sena '{etiqueta}' eliminada correctamente.")
    print(f"Muestras restantes: {len(datos_filtrados)}")


def main():
    parser = argparse.ArgumentParser(description="Borrar una sena completa del dataset LSC.")
    parser.add_argument("sena", nargs="?", help="Nombre de la sena que desea borrar.")
    parser.add_argument("--si", action="store_true", help="Confirma el borrado sin preguntar.")
    args = parser.parse_args()

    dataset, datos = cargar_dataset()

    if datos is None:
        print("Todavia no existe el dataset.")
        return

    if not args.sena:
        print(f"Dataset: {dataset}")
        listar_senas(datos)
        return

    borrar_sena(args.sena, confirmar=args.si)


if __name__ == "__main__":
    main()
