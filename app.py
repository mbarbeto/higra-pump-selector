import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Higra Pump Selector", layout="wide")
st.image("logo_higra.png", width=250)
st.markdown("##### Powered by Bauzi Tech")
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
    tol_v = vazao_req * 0.10
    tol_p = pressao_req * 0.10

    candidatos = df[
        (abs(df["vazao"] - vazao_req) <= tol_v) &
        (abs(df["pressao"] - pressao_req) <= tol_p)
    ].copy()

    if candidatos.empty:
        return candidatos

    candidatos["erro_percentual"] = (
        abs(candidatos["vazao"] - vazao_req) / vazao_req +
        abs(candidatos["pressao"] - pressao_req) / pressao_req
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


if st.button("🔍 Buscar Modelo Ideal"):

    resultado = buscar_modelos(df_simples, vazao_req, pressao_req)
    origem = "Configuração Simples"

    if resultado.empty:
        resultado = buscar_modelos(df_paralelo, vazao_req, pressao_req)
        origem = "Configuração em Paralelo"

    if resultado.empty:
        resultado = buscar_modelos(df_serie, vazao_req, pressao_req)
        origem = "Configuração em Série"

    if resultado.empty:
        st.error("❌ Nenhum modelo padrão encontrado dentro da tolerância de ±10%. Consultar equipe técnica Higra.")
    else:
        st.success(f"✅ Modelos encontrados ({origem})")
        st.markdown("Tolerância considerada: ±10% para vazão e pressão.")
        st.markdown("---")

        melhor = resultado.iloc[0]

        st.markdown("### 🏆 Sugestão Principal")

        desvio_v = abs(melhor["vazao"] - vazao_req) / vazao_req * 100
        desvio_p = abs(melhor["pressao"] - pressao_req) / pressao_req * 100

        st.write(melhor["descricao"])
        st.write(f"📊 Desvio Vazão: {desvio_v:.2f}%")
        st.write(f"📊 Desvio Pressão: {desvio_p:.2f}%")
        st.write(f"📐 Erro Combinado Total: {melhor['erro_percentual'] * 100:.2f}%")

        st.markdown("---")
        st.markdown("### Outras alternativas")

        for i in range(1, len(resultado)):
            alt = resultado.iloc[i]

            st.write(alt["descricao"])
