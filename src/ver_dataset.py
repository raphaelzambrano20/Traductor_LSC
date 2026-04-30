import pandas as pd

from config import DATASET_PATH, ENTRADA_MODELO, LEGACY_DATASET_PATH


def ver_dataset():
    dataset = DATASET_PATH if DATASET_PATH.exists() else LEGACY_DATASET_PATH

    if not dataset.exists():
        print("Todavia no existe el dataset. Capture muestras primero.")
        return

    columnas = ["sena"] + [f"p{i}" for i in range(ENTRADA_MODELO)]
    datos = pd.read_csv(dataset, header=None, names=columnas, usecols=range(ENTRADA_MODELO + 1))
    resumen = datos["sena"].value_counts().sort_values(ascending=False)

    print(f"Dataset: {dataset}")
    print(f"Total de muestras: {len(datos)}")
    print(f"Total de senas: {resumen.shape[0]}")
    print("\nMuestras por sena:")
    print(resumen.to_string())

    print("\nUltimas 10 muestras:")
    print(datos[["sena"]].tail(10).to_string(index=False))


if __name__ == "__main__":
    ver_dataset()
