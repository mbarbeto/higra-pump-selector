import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Higra Pump Selector", layout="wide")

# Cabeçalho institucional
st.image("logo_higra.png", width=250)
st.markdown("##### Desenvolvido por bauzi tech")
st.markdown("---")

st.title("Assistente Técnico de Seleção de Bombas Higra")

st.markdown("Insira os dados do ponto de trabalho requerido:")

vazao_req = st.number_input("Vazão requerida (m³/h)", min_value=0.01, format="%.2f")
pressao_req = st.number_input("Pressão requerida (mca)", min_value=0.01, format="%.2f")


def carregar_dados(caminho):
    dados = []
    with open(caminho, "r", encoding="utf-8") as f:
        for linha in f:
            vazao_match = re.search(r"Vazão:\s*([\d\.]+)", linha)
            pressao_match = re.search(r"Pressão:\s*([\d\.]+)", linha)
            rendimento_match = re.search(r"Rendimento:\s*([\d\.]+)", linha)

            if vazao_match and pressao_match:
                vazao = float(vazao_match.group(1))
                pressao = float(pressao_match.group(1))
                rendimento = float(rendimento_match.group(1)) if rendimento_match else 0

                dados.append({
                    "descricao": linha.strip(),
                    "vazao": vazao,
                    "pressao": pressao,
                    "rendimento": rendimento
                })

    return pd.DataFrame(dados)


def buscar_modelos(df, vazao_req, pressao_req):

    # Regra: mínimo 0% abaixo, máximo +20% acima
    candidatos = df[
        (df["vazao"] >= vazao_req) &
        (df["vazao"] <= vazao_req * 1.20) &
        (df["pressao"] >= pressao_req) &
        (df["pressao"] <= pressao_req * 1.20)
    ].copy()

    if candidatos.empty:
        return candidatos

    # Cálculo do excesso percentual combinado
    candidatos["erro_percentual"] = (
        (candidatos["vazao"] - vazao_req) / vazao_req +
        (candidatos["pressao"] - pressao_req) / pressao_req
    )

    candidatos = candidatos.sort_values(
        by=["erro_percentual", "rendimento"],
        ascending=[True, False]
    )

    return candidatos


# Carregar bases
df_simples = carregar_dados("Pontos de Operação Bombas Higra-Simples.txt")
df_paralelo = carregar_dados("Pontos de Operação Bombas Higra-Paralelo.txt")
df_serie = carregar_dados("Pontos de Operação Bombas Higra-Série.txt")


if st.button("Buscar Modelo Ideal"):

    resultado = buscar_modelos(df_simples, vazao_req, pressao_req)
    origem = "Configuração Simples"

    if resultado.empty:
        resultado = buscar_modelos(df_paralelo, vazao_req, pressao_req)
        origem = "Configuração em Paralelo"

    if resultado.empty:
        resultado = buscar_modelos(df_serie, vazao_req, pressao_req)
        origem = "Configuração em Série"

    if resultado.empty:
        st.error("Nenhum modelo encontrado entre 0% e +20% acima do ponto requerido. Consultar equipe técnica Higra.")
    else:
        st.success(f"Modelos encontrados ({origem})")
        st.markdown("**Critério aplicado:** seleção entre 0% e +20% acima do ponto requerido.")
        st.markdown("---")

        melhor = resultado.iloc[0]

        st.markdown("## Sugestão Principal")

        desvio_v = (melhor["vazao"] - vazao_req) / vazao_req * 100
        desvio_p = (melhor["pressao"] - pressao_req) / pressao_req * 100
        erro_total = melhor["erro_percentual"] * 100

        st.markdown(f"**Modelo Selecionado:**  \n{melhor['descricao']}")
        st.markdown("---")

        col1, col2, col3 = st.columns(3)

        col1.markdown(f"**Excesso Vazão**  \n{desvio_v:.2f}%")
        col2.markdown(f"**Excesso Pressão**  \n{desvio_p:.2f}%")
        col3.markdown(f"**Excesso Combinado Total**  \n{erro_total:.2f}%")

        st.markdown("---")
        st.markdown("## Outras Alternativas")

        for i in range(1, len(resultado)):
            alt = resultado.iloc[i]
            st.markdown(f"- {alt['descricao']}")
