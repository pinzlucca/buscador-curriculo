import os
import shutil
import pdfplumber

# Configurações de pastas
BASE_DIR = os.path.dirname(__file__)
PASTA_CURRICULOS = os.path.join(BASE_DIR, '..', 'curriculos')
PASTA_RESULTADOS = os.path.join(BASE_DIR, '..', 'resultados')
os.makedirs(PASTA_RESULTADOS, exist_ok=True)

# Palavras-chave para buscar
PALAVRAS_CHAVE = ["limpeza"]

def contem_palavra_chave(texto, palavras_chave):
    texto_lower = texto.lower()
    return any(palavra.lower() in texto_lower for palavra in palavras_chave)

def buscar_palavras_em_curriculos():
    encontrados = []

    for arquivo in os.listdir(PASTA_CURRICULOS):
        if arquivo.endswith('.pdf'):
            caminho = os.path.join(PASTA_CURRICULOS, arquivo)
            try:
                with pdfplumber.open(caminho) as pdf:
                    texto = ''
                    for pagina in pdf.pages:
                        texto += pagina.extract_text() or ''
                    
                    if contem_palavra_chave(texto, PALAVRAS_CHAVE):
                        print(f"✅ Palavra-chave encontrada em: {arquivo}")
                        encontrados.append(arquivo)

                        # Copia o arquivo para pasta de resultados
                        destino = os.path.join(PASTA_RESULTADOS, arquivo)
                        shutil.copyfile(caminho, destino)

            except Exception as e:
                print(f"⚠️ Erro ao ler {arquivo}: {e}")
    
    print(f"\n🔍 Busca concluída. {len(encontrados)} arquivos encontrados.")
    return encontrados

if __name__ == "__main__":
    buscar_palavras_em_curriculos()
