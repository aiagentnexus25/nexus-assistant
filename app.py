import streamlit as st
from openai import OpenAI
import os
import time
import pandas as pd
from datetime import datetime
import plotly.express as px

# Configuração da página
st.set_page_config(
    page_title="NEXUS - Assistente de IA Acadêmico",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4527A0;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #5E35B1;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-container {
        border-radius: 10px;
        background-color: #F5F5F5;
        padding: 20px;
        margin-bottom: 20px;
    }
    .user-message {
        background-color: #E3F2FD;
        padding: 10px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 5px solid #2196F3;
    }
    .assistant-message {
        background-color: #E8F5E9;
        padding: 10px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 5px solid #4CAF50;
    }
    .sidebar-content {
        padding: 20px 10px;
    }
    .metric-card {
        background-color: #FAFAFA;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Inicialização da sessão
if 'client' not in st.session_state:
    st.session_state.client = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'token_usage' not in st.session_state:
    st.session_state.token_usage = {'prompt_tokens': 0, 'completion_tokens': 0}
if 'conversation_count' not in st.session_state:
    st.session_state.conversation_count = 0
if 'feedback_data' not in st.session_state:
    st.session_state.feedback_data = []
if 'api_key_configured' not in st.session_state:
    st.session_state.api_key_configured = False

# Sidebar para configuração
with st.sidebar:
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    st.image("https://via.placeholder.com/150x150.png?text=NEXUS", width=150)
    st.markdown("## Configurações")
    
    # API Key Input
    api_key = st.text_input("OpenAI API Key", type="password", help="Insira sua chave de API da OpenAI")
    
    if api_key:
        try:
            st.session_state.client = OpenAI(api_key=api_key)
            if not st.session_state.api_key_configured:
                st.session_state.api_key_configured = True
                st.success("API configurada com sucesso!")
        except Exception as e:
            st.error(f"Erro ao configurar a API: {e}")
    
    # Configurações do modelo
    st.markdown("### Modelo e Parâmetros")
    model = st.selectbox("Modelo", ["gpt-3.5-turbo", "gpt-4o", "gpt-4"])
    temperature = st.slider("Temperatura", 0.0, 1.0, 0.7, 0.1)
    
    # Exibir métricas
    st.markdown("### Métricas")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Conversas", st.session_state.conversation_count)
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Tokens Usados", st.session_state.token_usage['prompt_tokens'] + st.session_state.token_usage['completion_tokens'])
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Botão para limpar o chat
    if st.button("Novo Chat"):
        st.session_state.messages = []
        st.session_state.conversation_count += 1
    
    # Botão para exportar histórico
    if st.button("Exportar Histórico"):
        if st.session_state.chat_history:
            df = pd.DataFrame(st.session_state.chat_history)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Baixar CSV",
                csv,
                f"nexus_chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv",
                key='download-csv'
            )
        else:
            st.warning("Nenhum histórico disponível para exportar.")
    
    # Feedback
    st.markdown("### Feedback")
    feedback = st.radio("Como está sua experiência?", ["😀 Excelente", "🙂 Boa", "😐 Neutra", "🙁 Ruim", "😞 Péssima"])
    feedback_text = st.text_area("Comentários adicionais")
    
    if st.button("Enviar Feedback"):
        st.session_state.feedback_data.append({
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'rating': feedback,
            'comments': feedback_text
        })
        st.success("Feedback enviado. Obrigado!")
    
    st.markdown("</div>", unsafe_allow_html=True)

# Função para gerar resposta
def generate_response(prompt, model, temperature):
    if not st.session_state.client:
        return "Por favor, configure sua API key na barra lateral."
    
    try:
        messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        
        with st.spinner("NEXUS está processando..."):
            response = st.session_state.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature
            )
        
        # Atualizar uso de tokens
        st.session_state.token_usage['prompt_tokens'] += response.usage.prompt_tokens
        st.session_state.token_usage['completion_tokens'] += response.usage.completion_tokens
        
        # Adicionar à base de dados para análise
        st.session_state.chat_history.append({
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'user_message': prompt,
            'assistant_message': response.choices[0].message.content,
            'model': model,
            'temperature': temperature,
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens
        })
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"Erro ao gerar resposta: {str(e)}"

# Sistema de instruções personalizado para o NEXUS
nexus_instructions = """
Você é NEXUS, um assistente de IA especializado para pesquisadores e acadêmicos. Sua função é auxiliar em todas as etapas do trabalho acadêmico, desde a concepção de ideias até a publicação.

Competências:
1. Formulação de perguntas de pesquisa e hipóteses
2. Sugestão de métodos e abordagens metodológicas
3. Revisão de literatura e recomendação de fontes
4. Análise crítica de argumentos e resultados
5. Sugestão de estruturas para artigos e apresentações
6. Formatação e verificação de referências bibliográficas
7. Explicação de conceitos complexos de forma acessível

Ao responder:
- Forneça informações precisas e baseadas em evidências
- Quando relevante, indique limitações do seu conhecimento
- Ofereça perspectivas diversas sobre tópicos controversos
- Use linguagem técnica apropriada à área do conhecimento
- Priorize recursos e métodos recentes e bem estabelecidos

Você é um assistente amigável, respeitoso e útil, focado em potencializar o trabalho acadêmico de alta qualidade.
"""

# Carregar mensagem de sistema
if len(st.session_state.messages) == 0:
    st.session_state.messages.append({"role": "system", "content": nexus_instructions})

# Interface principal
st.markdown('<h1 class="main-header">NEXUS</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Assistente de IA Especializado para Pesquisadores e Acadêmicos</p>', unsafe_allow_html=True)

# Área de chat
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for message in st.session_state.messages:
    if message["role"] != "system":  # Não mostrar mensagens do sistema
        if message["role"] == "user":
            st.markdown(f'<div class="user-message">👤 <b>Você:</b> {message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="assistant-message">🧠 <b>NEXUS:</b> {message["content"]}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Input do usuário
prompt = st.text_area("Digite sua pergunta ou instrução para o NEXUS:", key="input")

# Verificar se o usuário digitou algo
if st.button("Enviar") and prompt:
    # Adicionar mensagem do usuário ao histórico
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Exibir imediatamente a mensagem do usuário
    st.markdown(f'<div class="user-message">👤 <b>Você:</b> {prompt}</div>', unsafe_allow_html=True)
    
    # Gerar resposta
    if st.session_state.api_key_configured:
        response = generate_response(prompt, model, temperature)
        # Adicionar resposta ao histórico
        st.session_state.messages.append({"role": "assistant", "content": response})
        # Exibir resposta do assistente
        st.markdown(f'<div class="assistant-message">🧠 <b>NEXUS:</b> {response}</div>', unsafe_allow_html=True)
    else:
        st.warning("Por favor, configure sua API key da OpenAI na barra lateral para continuar.")
    
    # Recarregar para limpar o input
    st.experimental_rerun()

# Dashboard para análise de uso (aba alternativa)
tab1, tab2 = st.tabs(["Chat", "Análise de Uso"])

with tab2:
    st.markdown("## Análise de Uso do NEXUS")
    
    if st.session_state.chat_history:
        # Converter histórico para DataFrame
        history_df = pd.DataFrame(st.session_state.chat_history)
        
        # Mostrar estatísticas gerais
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Interações", len(history_df))
        with col2:
            st.metric("Tokens Prompt", st.session_state.token_usage['prompt_tokens'])
        with col3:
            st.metric("Tokens Completion", st.session_state.token_usage['completion_tokens'])
        
        # Gráfico de tokens por conversa
        if len(history_df) > 1:
            history_df['total_tokens'] = history_df['prompt_tokens'] + history_df['completion_tokens']
            history_df['interaction_number'] = range(1, len(history_df) + 1)
            
            fig = px.line(history_df, x='interaction_number', y='total_tokens', 
                          title='Uso de Tokens por Interação')
            st.plotly_chart(fig, use_container_width=True)
        
        # Mostrar histórico recente
        st.markdown("### Histórico Recente")
        st.dataframe(
            history_df[['timestamp', 'user_message', 'assistant_message', 'model', 'total_tokens']]
            .sort_values('timestamp', ascending=False)
            .head(5)
        )
    else:
        st.info("Nenhum dado de uso disponível ainda. Comece a conversar com o NEXUS para gerar estatísticas.")

# Rodapé com créditos
st.markdown("""
---
<div style="text-align: center; color: gray; font-size: 0.8rem;">
    NEXUS - Assistente de IA Acadêmico | Desenvolvido com Streamlit e OpenAI
</div>
""", unsafe_allow_html=True)
