"""Validação e armazenamento das imagens dos produtos (RF-04, RNF-04, RNF-05)."""
import io
import os
import re
import secrets
import threading
from pathlib import Path

from PIL import Image, ImageCms, ImageOps

from app.config import uploads_dir

TAMANHO_MAXIMO = 2 * 1024 * 1024  # 2 MB
# Nome gerado pela aplicação: 32 hex + extensão. Só isso é servido de volta.
NOME_VALIDO = re.compile(r"[0-9a-f]{32}\.(jpg|png|webp)")
LADO_MAXIMO = 10_000  # px
AREA_MAXIMA = 50_000_000  # pixels (50 megapixels)
QUALIDADE = 90  # JPEG e WebP
FORMATOS = ["JPEG", "PNG", "WEBP"]  # decodificadores permitidos (CS-03)
FORMATO_DA_EXT = {"jpg": "JPEG", "png": "PNG", "webp": "WEBP"}
ORCAMENTO_PIXELS = AREA_MAXIMA  # pixels em decodificacao ao mesmo tempo, somando as requisicoes (CS-08)
ESPERA_MAXIMA = 30  # segundos esperando o orcamento (CS-08)
ERRO_CORROMPIDA = "A imagem está corrompida ou não pôde ser lida."
ERRO_DIMENSAO = "A imagem deve ter no máximo 10.000 px de lado e 50 megapixels."
ERRO_OCUPADO = "Servidor ocupado, tente de novo."
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


class ServidorOcupado(Exception):
    """Todas as vagas de decodificação ocupadas além da espera máxima (CS-08, 503)."""


class _OrcamentoPixels:
    """Semaforo ponderado: cada decodificacao reserva largura x altura de um total (SEC-T0010-01).

    Uma imagem de 50 MP ocupa tudo e roda sozinha; varias pequenas rodam juntas.
    """

    def __init__(self, total: int):
        self.total = total
        self.usado = 0
        self._cond = threading.Condition()

    def reservar(self, pixels: int, espera: float) -> bool:
        with self._cond:
            ok = self._cond.wait_for(lambda: self.usado + pixels <= self.total, timeout=espera)
            if ok:
                self.usado += pixels
            return ok

    def liberar(self, pixels: int) -> None:
        with self._cond:
            self.usado -= pixels
            self._cond.notify_all()


_ORCAMENTO = _OrcamentoPixels(ORCAMENTO_PIXELS)


def _dimensao_ok(largura: int, altura: int) -> bool:
    return max(largura, altura) <= LADO_MAXIMO and largura * altura <= AREA_MAXIMA


def _icc_reserializado(icc: bytes | None) -> bytes | None:
    """ICC só se o LittleCMS o ler; grava os bytes reserializados, nunca os recebidos (CS-06)."""
    if not icc:
        return None
    try:
        return ImageCms.ImageCmsProfile(io.BytesIO(icc)).tobytes()
    except Exception:
        return None


def _modo_para(im: Image.Image, ext: str) -> Image.Image:
    """Converte para um modo que o formato de saída aceita, mantendo a transparência."""
    if im.mode.startswith("I"):  # PNG de 16 bits em cinza: convert("RGB") satura (BUG-T0010-01)
        im = im.convert("I").point(lambda v: v / 257 + 0.5).convert("L")
    com_alfa = "A" in im.getbands() or "transparency" in im.info
    if ext == "jpg":
        return im if im.mode in ("L", "RGB", "CMYK") else im.convert("RGB")
    if ext == "png":
        if im.mode in ("1", "L", "RGB", "RGBA", "LA") and "transparency" not in im.info:
            return im
        return im.convert("RGBA" if com_alfa else "RGB")
    if im.mode in ("RGB", "RGBA") and "transparency" not in im.info:
        return im  # webp: ja no modo de saida, sem copia da imagem inteira
    return im.convert("RGBA" if com_alfa else "RGB")  # webp


def _regravar(conteudo: bytes, ext: str) -> tuple[bytes | None, str | None]:
    """Decodifica e regrava a imagem. Retorna (bytes, erro). Nunca levanta (exceto ServidorOcupado)."""
    try:
        with Image.open(io.BytesIO(conteudo), formats=FORMATOS) as im:
            formato = "JPEG" if im.format == "MPO" else im.format
            if formato != FORMATO_DA_EXT[ext]:
                return None, ERRO_CORROMPIDA
            if not _dimensao_ok(*im.size):  # só o cabeçalho foi lido: pixels não decodificados
                return None, ERRO_DIMENSAO
            pixels = im.size[0] * im.size[1]
            if not _ORCAMENTO.reservar(pixels, ESPERA_MAXIMA):  # antes de load() (SEC-T0010-01)
                raise ServidorOcupado
            try:
                return _decodificar_e_gravar(im, ext), None
            finally:
                _ORCAMENTO.liberar(pixels)
    except ServidorOcupado:
        raise
    except Image.DecompressionBombError:
        return None, ERRO_DIMENSAO
    except Exception:  # SyntaxError, ValueError, OSError, MemoryError... nada vira 500 (CS-02)
        return None, ERRO_CORROMPIDA


def _decodificar_e_gravar(im: Image.Image, ext: str) -> bytes:
    im.load()
    icc = _icc_reserializado(im.info.get("icc_profile"))
    transparencia = im.info.get("transparency")
    # sem orientacao a aplicar, nao copia a imagem inteira (menor pico de memoria)
    im2 = ImageOps.exif_transpose(im) if im.getexif().get(0x0112, 1) != 1 else im
    im2.load()
    if transparencia is not None:
        im2.info["transparency"] = transparencia
    saida = _modo_para(im2, ext)
    if saida.mode == "CMYK" and ext != "jpg":
        icc = None
    saida.info = {}  # nada de EXIF, XMP, comentário COM ou texto PNG herdado (CS-05)
    buf = io.BytesIO()
    opcoes: dict = {"icc_profile": icc} if icc else {}
    if ext == "jpg":
        saida.save(buf, "JPEG", quality=QUALIDADE, **opcoes)
    elif ext == "webp":
        saida.save(buf, "WEBP", quality=QUALIDADE, **opcoes)
    else:
        saida.save(buf, "PNG", **opcoes)
    return buf.getvalue()


def processar_imagem(conteudo: bytes) -> tuple[str | None, bytes | None, str | None]:
    """Retorna (extensao, bytes_regravados, erro). Conteúdo vazio é tratado antes (= sem imagem)."""
    if len(conteudo) > TAMANHO_MAXIMO:
        return None, None, "A imagem deve ter no máximo 2 MB."
    ext = detectar_tipo(conteudo)
    if ext is None:
        return None, None, "A imagem deve ser JPEG, PNG ou WebP."
    dados, erro = _regravar(conteudo, ext)
    if erro:
        return None, None, erro
    return ext, dados, None


def salvar(conteudo: bytes, ext: str) -> str:
    """Grava no volume com nome aleatório e devolve o nome (nunca usa o nome enviado).

    Escreve num temporário da mesma pasta e troca com os.replace (CS-09).
    """
    pasta = Path(uploads_dir())
    pasta.mkdir(parents=True, exist_ok=True)
    nome = f"{secrets.token_hex(16)}.{ext}"
    temporario = pasta / f".{secrets.token_hex(16)}.tmp"
    try:
        temporario.write_bytes(conteudo)
        os.replace(temporario, pasta / nome)
    except BaseException:
        temporario.unlink(missing_ok=True)
        raise
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
