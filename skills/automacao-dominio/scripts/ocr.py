"""OCR local (Windows.Media.Ocr, sem custo de tokens). ler(imagem_PIL) -> texto.
Usado para LER campos (empresa ativa, datas) antes de preencher. Uso: python ocr.py arquivo.png"""
import asyncio
import io
import sys

from PIL import Image
from winrt.windows.globalization import Language
from winrt.windows.graphics.imaging import BitmapDecoder
from winrt.windows.media.ocr import OcrEngine
from winrt.windows.storage.streams import DataWriter, InMemoryRandomAccessStream


async def _ler(img, palavras=False):
    buf = io.BytesIO()
    img.save(buf, "PNG")
    st = InMemoryRandomAccessStream()
    w = DataWriter(st)
    w.write_bytes(buf.getvalue())
    await w.store_async()
    st.seek(0)
    bmp = await (await BitmapDecoder.create_async(st)).get_software_bitmap_async()
    eng = OcrEngine.try_create_from_language(Language("pt-BR")) or OcrEngine.try_create_from_user_profile_languages()
    res = await eng.recognize_async(bmp)
    if palavras:
        return [(w.text, w.bounding_rect.x, w.bounding_rect.y, w.bounding_rect.width, w.bounding_rect.height)
                for ln in res.lines for w in ln.words]
    return res.text


def ler(img, escala=3):
    img = img.convert("RGB")
    img = img.resize((img.width * escala, img.height * escala), Image.LANCZOS)   # OCR vai melhor em fonte maior
    return asyncio.run(_ler(img))


def palavras(img, escala=2):
    """[(texto, x, y, w, h)] em coordenadas da imagem original."""
    img = img.convert("RGB")
    g = img.resize((img.width * escala, img.height * escala), Image.LANCZOS)
    return [(t, x / escala, y / escala, w / escala, h / escala) for t, x, y, w, h in asyncio.run(_ler(g, True))]


if __name__ == "__main__":
    print(ler(Image.open(sys.argv[1])))
