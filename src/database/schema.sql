PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    descripcion TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS senas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    palabra TEXT NOT NULL UNIQUE,
    categoria_id INTEGER NOT NULL,
    descripcion TEXT NOT NULL DEFAULT '',
    ruta_video TEXT,
    ruta_imagen TEXT,
    activo INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id)
);

CREATE TABLE IF NOT EXISTS frases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    texto TEXT NOT NULL UNIQUE,
    categoria_id INTEGER NOT NULL,
    descripcion TEXT NOT NULL DEFAULT '',
    ruta_video TEXT,
    activo INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id)
);

CREATE TABLE IF NOT EXISTS sinonimos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sena_id INTEGER,
    frase_id INTEGER,
    texto TEXT NOT NULL UNIQUE,
    FOREIGN KEY (sena_id) REFERENCES senas(id),
    FOREIGN KEY (frase_id) REFERENCES frases(id),
    CHECK (
        (sena_id IS NOT NULL AND frase_id IS NULL)
        OR (sena_id IS NULL AND frase_id IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_senas_categoria ON senas(categoria_id);
CREATE INDEX IF NOT EXISTS idx_frases_categoria ON frases(categoria_id);
