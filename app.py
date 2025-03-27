import streamlit as st
import ollama
from PIL import Image
import io
import pybase64
from groq import Groq
from textwrap import dedent
from dotenv import load_dotenv
import os
import pandas as pd

# Configura o pandas para exibir floats com 2 casas decimais
pd.set_option('display.float_format', '{:.2f}'.format)

# Page configuration
st.set_page_config(
    page_title="Leitor de Etiqueta",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Listas para armazenar os dados
lista_produto = []
lista_preco = []
lista_imagem = []
lista_etiqueta = []

llama_mm = 'llama-3.2-11b-vision-preview'  # Modelo Multi Modal para ler a imagem e descrever

# Carregar variáveis de ambiente
load_dotenv()

# Obter a chave da API GROQ
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Função para codificar a imagem em base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return pybase64.b64encode(image_file.read()).decode('utf-8')

# Função para converter imagem em texto usando o modelo GROQ
def image_to_text(model, b64_image, prompt):
    client = Groq(api_key=GROQ_API_KEY)

    result = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": [
                    {'type': 'text', 'text': prompt},
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': f"data:image/jpeg;base64,{b64_image}",
                        },
                    },
                ],
            }
        ],
        model=model,
        temperature=.2,  # Controla a criatividade
        top_p=0.1,  # Controla a diversidade das respostas
    )

    return result.choices[0].message.content


# Interface do Streamlit

img = Image.open('imgs/caixa.png')
image_path="image.png"
img.save(image_path)
# Getting the base64 string
base64_image = encode_image(image_path)
# Usando HTML para centralizar a imagem
st.sidebar.markdown(
        f"""
        <div style="display: flex; justify-content: center;">
            <img src="data:image/png;base64,{base64_image}" alt="Imagem" style="width: auto; height: auto;">
        </div>
        """,
        unsafe_allow_html=True
    )

html_page_title = """
<div style="background-color:black;padding=60px">
        <p style='text-align:center;font-size:50px;font-weight:bold; color:red'>Leitor de Etiquetas de Preço</p>
</div>
"""               
st.markdown(html_page_title, unsafe_allow_html=True)



st.subheader(f"Modelo: {llama_mm}")

# Botão para limpar resultados
col1, col2 = st.columns([6, 1])
#with col2:
#    if st.button("Clear 🗑️"):
#        if 'ocr_result' in st.session_state:
#            del st.session_state['ocr_result']
#            lista_produto.clear()
#            lista_preco.clear()
#            lista_etiqueta.clear()
#        st.rerun()

# Barra lateral para upload de imagens
with st.sidebar:
    st.header("Etiquetas nas prateleiras")
    uploaded_files = st.file_uploader(
        "Selecione as imagens",
        type=["jpg", "jpeg", "png", "gif", "bmp"],  # Tipos de arquivo permitidos
        accept_multiple_files=True  # Permite upload de vários arquivos
    )

    # Verifica se arquivos foram carregados
    if uploaded_files:
        st.success(f"{len(uploaded_files)} imagem(ns) carregada(s) com sucesso!")
    else:
        st.warning("Nenhuma imagem carregada ainda.")

    # Exibe as imagens carregadas
    for img_nome in uploaded_files:
        image = Image.open(img_nome)
        st.image(image, caption=img_nome.name, use_container_width=True)
    
    lidos = len(uploaded_files)
    st.subheader(f"{lidos} etiquetas")
    n = 1
    # Botão para extrair texto
    if st.button("Extract Text 🔍", type="primary"):
        with st.spinner("Processando imagens..."):
            for img_nome in uploaded_files:
                st.write(f'{n} de {lidos}')
                st.write(f"Processando: {img_nome.name}")
                try:
                    # Salva a imagem temporariamente
                    image = Image.open(img_nome)
                    image_path = f"temp_{img_nome.name}"
                    image.save(image_path)

                    # Codifica a imagem em base64
                    base64_image = encode_image(image_path)

                    # Prompt para extrair informações
                    prompt = ("""         
                        You are an expert assistant in recognizing and describing images with precision.
                        Dont anwer steps done to extract product name and price. Only final answer accordint to template.
                        Extract product names, prices in image.
                        Products must only appear once in the answer.
                        Look for price for label 'EXCLUSIVO PARA COOPERADOS' OR 'COOPERADOS' OR 'PRECO NORMAL.
                        Always answer to price less expensisve only.
                        Discounted price starts with 'POR R$'
                        At answer in Portuguese, return only it:
                        Produto: Name
                        Preço: R$ discounted price (less expensive)
                        Follow this template: 
                        Produto: nome do produto
                        Preço: preço do produto
                    """)

                    # Chama a função para processar a imagem
                    descricao = image_to_text(llama_mm, base64_image, prompt)

                    # Extrai o produto e o preço da descrição
                    try:
                        texto = descricao
                        lista_etiqueta.append(texto)
                        lista_imagem.append(f'{img_nome.name}')
                        n = n + 1
                    except Exception as e:
                        st.error(f"Erro ao processar a descrição: {e}")

                    # Remove a imagem temporária
                    os.remove(image_path)

                except Exception as e:
                    st.error(f"Erro ao processar a imagem {img_nome.name}: {str(e)}")

# Exibe os resultados
if len(lista_etiqueta) > 0:
    #st.write('Imagens:', lista_imagem)
    #st.write('Etiquetas:', lista_etiqueta)
    lidos = len(uploaded_files)
    #st.subheader(f"Foram lidas {lidos} etiquetas")

    # Processamento da lista
    produtos_unicos = set()  # Para garantir que os produtos sejam únicos
    n = 1
    for item in lista_etiqueta:
        # Remove caracteres extras (como **) e divide o item em linhas
        lines = item.replace("**", "").split("\n")
        
        #st.write(f"Itens {n}: {lines}")
        #n = n + 1
        # Extrai o nome do produto
        produto = lines[0].split("Produto:")[1].strip()
        # Pega apenas os dois primeiros termos do nome
        #produto = ' '.join(produto.split()[:2])
        
        # Extrai o preço
        preco = lines[1].split("Preço:")[1].strip()
        
        # Adiciona às listas apenas se o produto for único
        if produto not in produtos_unicos:
            produtos_unicos.add(produto)
            lista_produto.append(produto)
            lista_preco.append(preco)

    # Cria o DataFrame
    #st.write("Lista produto:", len(lista_produto))
    #st.write("Lista preço:", len(lista_preco))
    #st.write("Lista imagem:", len(lista_imagem))
    
    data = {'Imagem': lista_imagem, 'Produto': lista_produto,
             'Preço (R$)': lista_preco}
    df = pd.DataFrame(data)

    # Exibe o DataFrame
    #st.dataframe(df)

    # Processamento adicional dos preços
    df['Gasto'] = df['Preço (R$)'].str.replace('R$', '', regex=False).str.replace(',', '.', regex=False).str.strip().astype(float)
    df['Preço (R$)'] = df['Preço (R$)'].str.replace('R$', '', regex=False)
    #df['Preço (R$)'] = round(df['Preço (R$)'], 2)
    
    # Exibe a tabela final
    st.markdown("### Lista de Produtos e Preços")
    colunas = ['Imagem', 'Produto', 'Preço (R$)']
    st.table(df[colunas])    
    total_itens = str(df.shape[0])
    total_gasto = str(df['Gasto'].sum().round(2))
    #st.markdown(f"### Total de itens: {total_itens} \tGasto: R$ {total_gasto}")
    st.markdown("### Gasto: R$ " + total_gasto)
    
else:
    st.info("Faça upload das imagens e clique em 'Extract Text' para ver os resultados.")