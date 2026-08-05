"""
Extraction du texte brut d'un fichier source (Word, PDF, scan, photo),
première étape du pipeline. La deuxième étape (parsing des champs) est
dans parsing.py.

Méthode choisie selon Document.type_document :
- word   -> lecture directe du texte (.docx), le plus fiable
- pdf    -> extraction du texte natif si le PDF en contient (pdfplumber) ;
            sinon, le PDF est traité comme une image scannée (OCR)
- scanne -> OCR direct (le fichier est déjà une image scannée)
- photo  -> OCR avec un prétraitement d'image plus poussé (la source est
            plus bruitée : angle, éclairage, arrière-plan)
"""
import pytesseract
from PIL import Image, ImageOps


def extraire_texte_word(chemin_fichier):
    import docx

    doc = docx.Document(chemin_fichier)
    paragraphes = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphes)


def extraire_texte_pdf(chemin_fichier):
    import pdfplumber

    textes = []
    with pdfplumber.open(chemin_fichier) as pdf:
        for page in pdf.pages:
            texte_page = page.extract_text()
            if texte_page:
                textes.append(texte_page)

    texte_natif = "\n".join(textes).strip()
    if texte_natif:
        return texte_natif

    # Aucun texte natif trouvé : le PDF est probablement un scan
    # (image encapsulée dans un PDF) -> on rasterise chaque page et on
    # applique l'OCR, comme pour un scan/photo classique.
    from pdf2image import convert_from_path

    pages = convert_from_path(chemin_fichier)
    textes_ocr = [_ocr_image(page, photo=False) for page in pages]
    return "\n".join(textes_ocr)


def _pretraiter_image(image: Image.Image, photo: bool) -> Image.Image:
    """
    Prétraitement avant OCR. Le simple passage en niveaux de gris +
    autocontrast s'est avéré, à l'usage sur des photos réelles, plus
    fiable qu'un traitement plus agressif (une égalisation d'histogramme
    testée initialement dégradait nettement la reconnaissance sur des
    photos de documents avec un éclairage déjà correct -- à ajuster si
    de futures photos plus difficiles (contre-jour, faible contraste)
    montrent l'inverse).
    """
    image = ImageOps.grayscale(image)
    image = ImageOps.autocontrast(image)
    return image


def _ocr_image(image: Image.Image, photo: bool) -> str:
    image_pretraitee = _pretraiter_image(image, photo=photo)
    return pytesseract.image_to_string(image_pretraitee, lang="fra")


def extraire_texte_image(chemin_fichier, photo: bool) -> str:
    image = Image.open(chemin_fichier)
    return _ocr_image(image, photo=photo)


def extraire_texte(chemin_fichier: str, type_document: str) -> str:
    """
    Point d'entrée principal : dispatch selon le type de document.
    Lève une exception si le type n'est pas reconnu ou si l'extraction
    échoue -- à l'appelant (commande CLI, ou plus tard une vue d'upload)
    de décider quoi faire (marquer le Document en "rejetee", par ex.).
    """
    if type_document == "word":
        return extraire_texte_word(chemin_fichier)
    if type_document == "pdf":
        return extraire_texte_pdf(chemin_fichier)
    if type_document == "scanne":
        return extraire_texte_image(chemin_fichier, photo=False)
    if type_document == "photo":
        return extraire_texte_image(chemin_fichier, photo=True)
    raise ValueError(f"Type de document non reconnu : {type_document!r}")


def deviner_type_document(chemin_fichier: str) -> str:
    """
    Déduit le type_document à partir de l'extension du fichier, à défaut
    d'une indication explicite fournie par l'utilisateur. 'scanne' vs
    'photo' ne peut pas se déduire de l'extension seule (les deux sont
    souvent des .jpg/.png) -- l'appelant doit préciser --type dans ce cas,
    sinon 'photo' est utilisé par défaut (traitement le plus prudent, avec
    le prétraitement le plus poussé).
    """
    ext = chemin_fichier.lower().rsplit(".", 1)[-1]
    if ext in ("docx",):
        return "word"
    if ext in ("pdf",):
        return "pdf"
    if ext in ("jpg", "jpeg", "png", "webp", "bmp", "tiff"):
        return "photo"
    raise ValueError(
        f"Impossible de deviner le type de document pour l'extension .{ext} "
        "-- précisez --type explicitement (word/pdf/scanne/photo)."
    )
