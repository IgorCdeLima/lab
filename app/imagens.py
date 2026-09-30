"""Validação e armazenamento das imagens dos produtos (RF-04, RNF-04, RNF-05)."""
import re
import secrets
from pathlib import Path

from app.config import uploads_dir

TAMANHO_MAXIMO = 2 * 1024 * 1024  # 2 MB
# Nome gerado pela aplicação: 32 hex + extensão. Só isso é servido de volta.
NOME_VALIDO = re.compile(r"[0-9a-f]{32}\.(jpg|png|webp)")
TIPOS = {"jpg": "image/jpeg", "png": "image/png", "webp": "image/webp"}


def detectar_tipo(conteudo: bytes) -> str | None:
    """Extensão ('jpg', 'png', 'webp') pelos bytes iniciais; None se não for imagem aceita."""
    if conteudo.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if conteudo.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if conteudo[:4] == b"RIFF" and conteudo[8:12] == b"WEBP":
        return "webp"
    return None


def validar_imagem(conteudo: bytes) -> tuple[str | None, str | None]:
    """Retorna (extensao, erro). Conteúdo vazio deve ser tratado antes (= sem imagem)."""
    if len(conteudo) > TAMANHO_MAXIMO:
        return None, "A imagem deve ter no máximo 2 MB."
    ext = detectar_tipo(conteudo)
    if ext is None:
        return None, "A imagem deve ser JPEG, PNG ou WebP."
    return ext, None


def salvar(conteudo: bytes, ext: str) -> str:
    """Grava no volume com nome aleatório e devolve o nome (nunca usa o nome enviado)."""
    pasta = Path(uploads_dir())
    pasta.mkdir(parents=True, exist_ok=True)
    nome = f"{secrets.token_hex(16)}.{ext}"
    (pasta / nome).write_bytes(conteudo)
    return nome


def remover(nome: str) -> None:
    if NOME_VALIDO.fullmatch(nome):
        (Path(uploads_dir()) / nome).unlink(missing_ok=True)


def caminho(nome: str) -> Path | None:
    """Caminho do arquivo se o nome for do formato gerado e existir; senão None."""
    if not NOME_VALIDO.fullmatch(nome):
        return None
    p = Path(uploads_dir()) / nome
    return p if p.is_file() else None
