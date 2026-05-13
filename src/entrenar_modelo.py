import csv
import os

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import joblib
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

from config import DATASET_PATH, ENTRADA_MODELO, LEGACY_DATASET_PATH, MODEL_PATH, MODELS_DIR


def crear_modelos():
    return {
        "RandomForest": RandomForestClassifier(
            n_estimators=200,
            random_state=42,
            n_jobs=1,
            class_weight="balanced_subsample",
        ),
        "ExtraTrees": ExtraTreesClassifier(
            n_estimators=300,
            random_state=42,
            n_jobs=1,
            class_weight="balanced",
        ),
        "HistGradientBoosting": HistGradientBoostingClassifier(
            max_iter=200,
            learning_rate=0.08,
            random_state=42,
        ),
    }


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

    resultados = []
    modelos = crear_modelos()

    print("\nEntrenando modelos candidatos...")
    for nombre_modelo, modelo_candidato in modelos.items():
        try:
            modelo_candidato.fit(X_train, y_train)
            predicciones = modelo_candidato.predict(X_test)
            precision = accuracy_score(y_test, predicciones)
            resultados.append(
                {
                    "nombre": nombre_modelo,
                    "modelo": modelo_candidato,
                    "precision": precision,
                    "predicciones": predicciones,
                }
            )
            print(f"- {nombre_modelo}: {precision:.2%}")
        except Exception as exc:
            print(f"- {nombre_modelo}: no se pudo entrenar ({exc})")

    if not resultados:
        print("No se pudo entrenar ningun modelo.")
        return

    mejor = max(resultados, key=lambda item: item["precision"])
    modelo = mejor["modelo"]
    predicciones = mejor["predicciones"]

    print("\nComparacion de modelos:")
    for resultado in sorted(resultados, key=lambda item: item["precision"], reverse=True):
        marca = " <- mejor" if resultado is mejor else ""
        print(f"{resultado['nombre']}: {resultado['precision']:.2%}{marca}")

    print(f"\nModelo guardado: {mejor['nombre']}")
    print("Precision del modelo:", mejor["precision"])
    print("\nReporte de clasificacion:")
    print(classification_report(y_test, predicciones, zero_division=0))

    MODELS_DIR.mkdir(exist_ok=True)
    artefacto = {
        "modelo": modelo,
        "nombre_modelo": mejor["nombre"],
        "precision": mejor["precision"],
        "modelos_evaluados": {
            resultado["nombre"]: resultado["precision"] for resultado in resultados
        },
        "n_features": X.shape[1],
        "tipo_caracteristicas": "holistic_temporal" if X.shape[1] > ENTRADA_MODELO else "holistic_postura",
    }
    joblib.dump(artefacto, MODEL_PATH)

    print(f"Modelo guardado en {MODEL_PATH}")


if __name__ == "__main__":
    entrenar_modelo()
