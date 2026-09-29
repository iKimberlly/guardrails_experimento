from pathlib import Path
import csv
import sqlite3

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = BASE_DIR / "guardrails.db"
VEICULOS_CSV = DATA_DIR / "veiculos.csv"

def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def get_user_vehicles(usuario_id: int):
    """Retorna somente veículos pertencentes ao usuário autenticado."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT id, usuario_id, categoria, placa, marca, modelo, ano,
               cidade, status, velocidade_kmh, latitude, longitude
        FROM veiculos
        WHERE usuario_id = ?
        ORDER BY id
    """, (usuario_id,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_user_vehicle(usuario_id: int, veiculo_id: int):
    """Retorna um veículo somente se pertencer ao usuário."""
    conn = get_connection()
    row = conn.execute("""
        SELECT id, usuario_id, categoria, placa, marca, modelo, ano,
               cidade, status, velocidade_kmh, latitude, longitude
        FROM veiculos
        WHERE id = ? AND usuario_id = ?
    """, (veiculo_id, usuario_id)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_positions(usuario_id: int, veiculo_id: int):
    """Retorna posições somente de veículo pertencente ao usuário."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT p.id, p.veiculo_id, p.data_hora,
               p.latitude, p.longitude, p.velocidade_kmh
        FROM posicoes p
        INNER JOIN veiculos v ON v.id = p.veiculo_id
        WHERE v.usuario_id = ? AND v.id = ?
        ORDER BY p.data_hora DESC
    """, (usuario_id, veiculo_id)).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def create_tables():
    conn = get_connection()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS usuarios(
        id INTEGER PRIMARY KEY,
        nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS veiculos(
        id INTEGER PRIMARY KEY,
        usuario_id INTEGER NOT NULL,
        categoria TEXT NOT NULL,
        placa TEXT UNIQUE NOT NULL,
        marca TEXT NOT NULL,
        modelo TEXT NOT NULL,
        ano INTEGER NOT NULL,
        cidade TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('ativo','em_manutencao','inativo')),
        velocidade_kmh REAL NOT NULL DEFAULT 0,
        latitude REAL,
        longitude REAL,
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
    );

    CREATE TABLE IF NOT EXISTS posicoes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        veiculo_id INTEGER NOT NULL,
        data_hora TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        velocidade_kmh REAL NOT NULL,
        FOREIGN KEY(veiculo_id) REFERENCES veiculos(id)
    );

    CREATE TABLE IF NOT EXISTS auditoria(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        acao TEXT NOT NULL,
        recurso TEXT,
        recurso_id INTEGER,
        permitido INTEGER NOT NULL CHECK(permitido IN (0,1)),
        motivo TEXT,
        data_hora TEXT NOT NULL,
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
    );
    """)
    conn.commit()
    conn.close()

def initialize_database():
    create_tables()

    with VEICULOS_CSV.open(encoding="utf-8-sig", newline="") as csv_file:
        vehicles = list(csv.DictReader(csv_file))

    user_ids = sorted({int(vehicle["usuario_id"]) for vehicle in vehicles})
    conn = get_connection()
    try:
        conn.executemany(
            """
            INSERT OR IGNORE INTO usuarios (id, nome, email)
            VALUES (?, ?, ?)
            """,
            [
                (user_id, f"Usuário de teste {user_id}", f"usuario{user_id}@example.test")
                for user_id in user_ids
            ],
        )
        conn.executemany(
            """
            INSERT OR IGNORE INTO veiculos (
                id, usuario_id, categoria, placa, marca, modelo, ano, cidade,
                status, velocidade_kmh, latitude, longitude
            )
            VALUES (
                :id, :usuario_id, :categoria, :placa, :marca, :modelo, :ano, :cidade,
                :status, :velocidade_kmh, :latitude, :longitude
            )
            """,
            vehicles,
        )
        conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    initialize_database()
    print(f"Banco: {DATABASE_PATH}")
    print(f"Dataset: {VEICULOS_CSV}")
