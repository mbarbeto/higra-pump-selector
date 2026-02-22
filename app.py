import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Higra Pump Selector", layout="wide")

# Cabeçalho institucional - Programado por: Marcio Barbeto
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
            potencia_match = re.search(r"Potência Demandada:\s*([\d\.]+)", linha)

            if vazao_match and pressao_match:
                vazao = float(vazao_match.group(1))
                pressao = float(pressao_match.group(1))
                rendimento = float(rendimento_match.group(1)) if rendimento_match else 0
                potencia = float(potencia_match.group(1)) if potencia_match else None

                dados.append({
                    "descricao": linha.strip(),
                    "vazao": vazao,
                    "pressao": pressao,
                    "rendimento": rendimento,
                    "potencia": potencia
                })

    return pd.DataFrame(dados)


def limpar_npsh_zero(texto):
    texto = re.sub(r"-\s*NPSH requerido:\s*0\s*mca\s*", "", texto)
    return texto


def buscar_modelos(df, vazao_req, pressao_req):

    limite_inf_v = vazao_req * 0.95
    limite_sup_v = vazao_req * 1.20

    limite_inf_p = pressao_req * 0.95
    limite_sup_p = pressao_req * 1.20

    candidatos = df[
        (df["vazao"] >= limite_inf_v) &
        (df["vazao"] <= limite_sup_v) &
        (df["pressao"] >= limite_inf_p) &
        (df["pressao"] <= limite_sup_p)
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
        st.error("Nenhum modelo padrão encontrado entre -5% e +20% do ponto requerido.")
    else:
        st.success(f"Modelos encontrados ({origem})")
        st.markdown("**Critério aplicado:** seleção entre -5% e +20% do ponto requerido.")
        st.markdown("---")

        # Melhor aproximação (já ordenado)
        melhor = resultado.iloc[0]

        # Menor potência
        menor_potencia = resultado.dropna(subset=["potencia"]).sort_values(by="potencia").iloc[0]

        st.markdown("## Melhor Aproximação ao Ponto de Trabalho")

        descricao_limpa = limpar_npsh_zero(melhor["descricao"])
        st.markdown(f"**Modelo Selecionado:**  \n{descricao_limpa}")

        st.markdown("---")

        # Só mostra seção se for diferente
        if menor_potencia.name != melhor.name:
            st.markdown("## Menor Consumo Energético")

            descricao_potencia = limpar_npsh_zero(menor_potencia["descricao"])
            st.markdown(f"**Modelo com Menor Potência Demandada:**  \n{descricao_potencia}")

            st.markdown("---")

        st.markdown("## Outras Alternativas")

        for i in range(1, len(resultado)):
            alt = resultado.iloc[i]
            descricao_alt = limpar_npsh_zero(alt["descricao"])
            st.markdown(f"- {descricao_alt}")




