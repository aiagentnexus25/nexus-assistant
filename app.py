import streamlit as st
import requests
import json
import time
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="NEXUS - Demo", page_icon="📋")

st.title("NEXUS - Assistente de Comunicação")
st.subheader("Versão de demonstração")

# Limites de uso
TOKEN_LIMIT = 3000
REQUEST_LIMIT = 5
RATE_LIMIT_SECONDS = 60

# Inicialização da sessão
if 'token_count' not in st.session_state:
    st.session_state.token_count = 0
if 'request_count' not in st.session_state:
    st.session_state.request_count = 0
if 'last_request_time' not in st.session_state:
    st.session_state.last_request_time = 0
if 'generated_content' not in st.session_state:
    st.session_state.generated_content = ""

# Carregar API key dos secrets
api_key = st.secrets.get("OPENAI_API_KEY", "")
if not api_key:
    st.error("API key não configurada. Por favor, contate o administrador.")

# Sidebar com informações de uso
with st.sidebar:
    st.header("Informações de Uso")
    st.progress(st.session_state.request_count / REQUEST_LIMIT)
    st.caption(f"Requisições: {st.session_state.request_count}/{REQUEST_LIMIT}")
    st.progress(st.session_state.token_count / TOKEN_LIMIT)
    st.caption(f"Tokens: {st.session_state.token_count}/{TOKEN_LIMIT}")
    
    st.markdown("---")
    st.caption("Esta é uma versão de demonstração limitada.")

# Função para gerar conteúdo
def generate_content(prompt, feature_type):
    # Verificar limites
    if st.session_state.token_count >= TOKEN_LIMIT:
        return "Limite de tokens excedido para esta sessão."
    if st.session_state.request_count >= REQUEST_LIMIT:
        return "Limite de requisições excedido para esta sessão."
    
    # Verificar rate limit
    current_time = time.time()
    if current_time - st.session_state.last_request_time < RATE_LIMIT_SECONDS and st.session_state.request_count > 0:
        wait_time = round(RATE_LIMIT_SECONDS - (current_time - st.session_state.last_request_time))
        return f"Por favor, aguarde {wait_time} segundos entre requisições."
    
    try:
        # Atualizar contadores
        st.session_state.last_request_time = current_time
        st.session_state.request_count += 1
        
        # Adicionar sistema de instruções básico
        system_message = "Você é NEXUS, um assistente especializado em comunicação de projetos."
        
        # API request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload),
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Atualizar tokens
            total_tokens = result['usage']['total_tokens']
            st.session_state.token_count += total_tokens
            
            return content
        else:
            return f"Erro na API (Status {response.status_code})"
    
    except Exception as e:
        return f"Erro: {str(e)}"

# Interface simplificada
st.info("Esta é uma versão simplificada do NEXUS com limites de uso para demonstração.")

feature = st.selectbox(
    "Selecione a funcionalidade",
    ["E-mail Profissional", "Agenda de Reunião", "Simplificação de Linguagem Técnica", 
     "Feedback Construtivo", "Análise de Riscos de Comunicação"]
)

with st.form("nexus_form"):
    context = st.text_area("Contexto do Projeto", 
                       placeholder="Descreva o projeto brevemente...",
                       height=100)
    
    content = st.text_area("Conteúdo ou pontos-chave", 
                       placeholder="Insira os detalhes específicos para sua solicitação...",
                       height=150)
    
    audience = st.text_input("Público-alvo", 
                         placeholder="Para quem esta comunicação se destina?")
    
    submit = st.form_submit_button("Gerar")

if submit:
    if not context or not content:
        st.warning("Por favor, preencha pelo menos os campos de contexto e conteúdo.")
    else:
        prompt = f"""
        Funcionalidade: {feature}
        
        Contexto do Projeto: {context}
        
        Conteúdo: {content}
        
        Público-alvo: {audience}
        
        Por favor, gere o conteúdo apropriado com base nas informações acima.
        """
        
        with st.spinner("Gerando resposta..."):
            result = generate_content(prompt, feature)
            st.session_state.generated_content = result
        
        st.subheader("Resultado")
        st.write(result)
        
        # Botão para download
        st.download_button(
            "Baixar como texto",
            result,
            file_name=f"nexus_{feature.lower().replace(' ', '_')}.txt",
            mime="text/plain"
        )

# Rodapé
st.markdown("---")
st.caption("NEXUS - Versão de Demonstração | © 2025")
