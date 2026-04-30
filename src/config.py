from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
DATASET_PATH = DATA_DIR / "senas.csv"
LEGACY_DATASET_PATH = DATA_DIR / "señas.csv"
MODEL_PATH = MODELS_DIR / "modelo_lsc.pkl"
LANDMARKS_POR_MANO = 21 * 3
MAX_MANOS = 2
ENTRADA_MODELO = LANDMARKS_POR_MANO * MAX_MANOS
