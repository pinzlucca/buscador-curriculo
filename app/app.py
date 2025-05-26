import os
import pdfplumber
import pytesseract
from PIL import Image
from docx import Document
import streamlit as st

# ✅ Importação segura do spaCy com fallback
import spacy
try:
    nlp = spacy.load("pt_core_news_sm")
except:
    import os
    os.system("python -m spacy download pt_core_news_sm")
    nlp = spacy.load("pt_core_news_sm")

# Caminho Tesseract (funciona apenas localmente – no Streamlit Cloud precisa adaptar)
# Se estiver no Streamlit Cloud, essa linha deve ser ignorada
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Caminho da pasta de currículos (certifique-se de que ela exista)
PASTA_CURRICULOS = os.path.join(os.path.dirname(__file__), 'curriculos')
os.makedirs(PASTA_CURRICULOS, exist_ok=True)

# 🧠 NLP: gera variações lematizadas da palavra e sinônimos simples
def gerar_variacoes(palavra):
    doc = nlp(palavra)
    lemas = set([token.lemma_.lower() for token in doc])

    sinonimos = {
        "limpeza": ["faxina", "faxineira", "zeladoria"],
        "motorista": ["condutor", "piloto", "chauffeur"],
        "segurança": ["vigilância", "vigilante", "porteiro", "controlador de acesso"],
        "atendimento": ["recepção", "recepcionista", "balconista"],
        "administração": ["gestão", "gerência", "administrativo"],
        "estoque": ["almoxarifado", "almoxarife", "armazenagem"]
    }

    extras = sinonimos.get(palavra.lower(), [])
    return lemas.union([s.lower() for s in extras])

# 📚 Funções de leitura
def ler_pdf(caminho):
    try:
        with pdfplumber.open(caminho) as pdf:
            texto = ''
            for pagina in pdf.pages:
                texto += pagina.extract_text() or ''
            return texto.lower()
    except:
        return ''

def ler_imagem(caminho):
    try:
        imagem = Image.open(caminho)
        texto = pytesseract.image_to_string(imagem, lang='por')
        return texto.lower()
    except:
        return ''

def ler_docx(caminho):
    try:
        doc = Document(caminho)
        texto = '\n'.join([p.text for p in doc.paragraphs])
        return texto.lower()
    except:
        return ''

def extrair_texto(caminho):
    ext = os.path.splitext(caminho)[1].lower()
    if ext == '.pdf':
        return ler_pdf(caminho)
    elif ext in ['.png', '.jpg', '.jpeg']:
        return ler_imagem(caminho)
    elif ext == '.docx':
        return ler_docx(caminho)
    else:
        return ''

# 🔍 Busca com lógica de pontuação
def buscar_palavra(palavra):
    resultados = []
    variacoes = gerar_variacoes(palavra)

    for arquivo in os.listdir(PASTA_CURRICULOS):
        caminho = os.path.join(PASTA_CURRICULOS, arquivo)
        if os.path.isfile(caminho):
            texto = extrair_texto(caminho)
            texto_limpo = texto.lower()

            score = 0
            total_ocorrencias = 0

            for termo in variacoes:
                ocorrencias = texto_limpo.count(termo.lower())
                total_ocorrencias += ocorrencias
                score += ocorrencias * 1

            trecho_inicial = texto_limpo[:500]
            if any(v in trecho_inicial for v in variacoes):
                score += 5

            trecho_destacado = "(Trecho não encontrado)"
            for termo in variacoes:
                idx = texto_limpo.find(termo)
                if idx != -1:
                    start = max(0, idx - 50)
                    end = min(len(texto_limpo), idx + 150)
                    trecho = texto[idx:end]
                    trecho_destacado = trecho.replace(termo, f"**{termo}**")
                    break

            if total_ocorrencias > 0:
                resultados.append({
                    "arquivo": arquivo,
                    "score": score,
                    "trecho": trecho_destacado
                })

    resultados.sort(key=lambda x: x["score"], reverse=True)
    return resultados

# 🌐 Interface com Streamlit
st.set_page_config(page_title="Buscador de Currículos", layout="centered")
st.title("🔎 Buscador de Currículos")
st.subheader("📤 Enviar novo currículo")
uploaded_file = st.file_uploader("Escolha um arquivo (PDF, DOCX, PNG, JPG)", type=["pdf", "docx", "png", "jpg", "jpeg"])

if uploaded_file is not None:
    nome_arquivo = uploaded_file.name
    caminho_salvo = os.path.join(PASTA_CURRICULOS, nome_arquivo)
    with open(caminho_salvo, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"Arquivo '{nome_arquivo}' enviado com sucesso!")

st.write("Pesquise currículos por qualquer palavra-chave. Suporte a PDF, imagem e Word.")

palavra_chave = st.text_input("Digite a palavra-chave", placeholder="Ex: segurança, limpeza, motorista")

if st.button("Buscar"):
    if not palavra_chave.strip():
        st.warning("Digite uma palavra válida para buscar.")
    else:
        encontrados = buscar_palavra(palavra_chave.strip())
        if encontrados:
            st.success(f"{len(encontrados)} currículo(s) encontrados com a palavra '{palavra_chave}':")
            for item in encontrados:
                caminho = os.path.join(PASTA_CURRICULOS, item["arquivo"])
                st.markdown(f"📄 **{item['arquivo']}** — 🏅 Pontuação: `{item['score']}`")
                st.markdown(f"🔍 _Trecho:_ {item['trecho']}")
                with open(caminho, "rb") as f:
                    st.download_button(label="📥 Baixar", data=f, file_name=item["arquivo"], mime="application/octet-stream")
        else:
            st.error("Nenhum currículo encontrado com essa palavra.")
