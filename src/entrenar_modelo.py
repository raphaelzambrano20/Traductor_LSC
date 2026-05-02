import csv

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

from config import DATASET_PATH, ENTRADA_MODELO, LEGACY_DATASET_PATH, MODEL_PATH, MODELS_DIR


def cargar_dataset_variable(archivo_csv):
    filas = []

    with archivo_csv.open("r", encoding="utf-8", newline="") as archivo:
        lector = csv.reader(archivo)
        for fila in lector:
            if fila and fila[0].strip():
                filas.append(fila)

    if not filas:
        return pd.Series(dtype=str), pd.DataFrame()

    max_columnas = max(len(fila) for fila in filas) - 1
    etiquetas = []
    caracteristicas = []

    for fila in filas:
        etiquetas.append(fila[0])
        valores = fila[1:]
        valores.extend([0.0] * (max_columnas - len(valores)))
        caracteristicas.append(valores)

    y = pd.Series(etiquetas)
    X = pd.DataFrame(caracteristicas).apply(pd.to_numeric, errors="coerce").fillna(0)
    return y, X


def entrenar_modelo():
    archivo_csv = DATASET_PATH if DATASET_PATH.exists() else LEGACY_DATASET_PATH

    if not archivo_csv.exists():
        print("No existe el dataset. Primero ejecute: python src/capturar_dataset.py")
        return

    y, X = cargar_dataset_variable(archivo_csv)

    if y.empty or X.empty:
        print("El dataset esta vacio o no tiene columnas suficientes.")
        return

    conteo_clases = y.value_counts()
    puede_estratificar = len(conteo_clases) > 1 and conteo_clases.min() >= 2

    if puede_estratificar:
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=42,
            stratify=y,
        )
    else:
        X_train, X_test, y_train, y_test = X, X, y, y
        print("Aviso: capture al menos 2 muestras por sena para evaluar con datos de prueba.")

    modelo = RandomForestClassifier(n_estimators=150, random_state=42)
    modelo.fit(X_train, y_train)

    predicciones = modelo.predict(X_test)
    precision = accuracy_score(y_test, predicciones)

    print("Precision del modelo:", precision)
    print("\nReporte de clasificacion:")
    print(classification_report(y_test, predicciones, zero_division=0))

    MODELS_DIR.mkdir(exist_ok=True)
    artefacto = {
        "modelo": modelo,
        "n_features": X.shape[1],
        "tipo_caracteristicas": "holistic_temporal" if X.shape[1] > ENTRADA_MODELO else "holistic_postura",
    }
    joblib.dump(artefacto, MODEL_PATH)

    print(f"Modelo guardado en {MODEL_PATH}")


if __name__ == "__main__":
    entrenar_modelo()
