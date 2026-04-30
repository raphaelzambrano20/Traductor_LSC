import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

from config import DATASET_PATH, ENTRADA_MODELO, LEGACY_DATASET_PATH, MODEL_PATH, MODELS_DIR


def entrenar_modelo():
    archivo_csv = DATASET_PATH if DATASET_PATH.exists() else LEGACY_DATASET_PATH

    if not archivo_csv.exists():
        print("No existe el dataset. Primero ejecute: python src/capturar_dataset.py")
        return

    datos = pd.read_csv(archivo_csv, header=None).dropna(how="all")

    if datos.empty or datos.shape[1] < 2:
        print("El dataset esta vacio o no tiene columnas suficientes.")
        return

    y = datos.iloc[:, 0]
    X = datos.iloc[:, 1 : ENTRADA_MODELO + 1].fillna(0)

    if X.shape[1] < ENTRADA_MODELO:
        faltantes = ENTRADA_MODELO - X.shape[1]
        columnas_extra = pd.DataFrame(0.0, index=X.index, columns=range(faltantes))
        X = pd.concat([X, columnas_extra], axis=1)

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
    joblib.dump(modelo, MODEL_PATH)

    print(f"Modelo guardado en {MODEL_PATH}")


if __name__ == "__main__":
    entrenar_modelo()
