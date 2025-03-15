import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import plotly.express as px
import os
import re
import docx
from io import BytesIO
import time

# ================= CONFIGURAÇÃO INICIAL =================

st.set_page_config(
    page_title="NEXUS - Assistente de Comunicação de Projetos",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paleta de cores
nexus_colors = {
    "purple": "#6247AA",
    "orange": "#FF6D2A",
    "teal": "#00C1D5",
    "dark_purple": "#231A41",
    "background": "#F5F5F7",
    "text_primary": "#1D1D1F",
    "text_secondary": "#86868B"
}

# CSS centralizado e minimalista
CUSTOM_CSS = f"""
<style>
  :root {{
    --purple: {nexus_colors['purple']};
    --orange: {nexus_colors['orange']};
    --teal: {nexus_colors['teal']};
    --dark-purple: {nexus_colors['dark_purple']};
    --background: {nexus_colors['background']};
    --text-primary: {nexus_colors['text_primary']};
    --text-secondary: {nexus_colors['text_secondary']};
  }}
  body {{
    font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background-color: var(--background);
    margin: 0;
    padding: 0;
  }}
  .header-gradient {{
    background: linear-gradient(90deg, var(--purple), var(--orange), var(--teal));
    padding: 1.5rem 2rem;
    border-radius: 10px;
    color: white;
    text-align: center;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  }}
  .sidebar-content {{
    padding: 1rem;
    text-align: center;
  }}
  .feature-card {{
    background-color: white;
    border-left: 4px solid var(--purple);
    border-radius: 10px;
    padding: 1rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
  }}
  .feature-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 4px 10px rgba(0,0,0,0.15);
  }}
  .button-primary {{
    background-color: var(--purple);
    color: white;
    border: none;
    border-radius: 50px;
    padding: 0.5rem 1.5rem;
    cursor: pointer;
    transition: background-color 0.2s;
    width: 100%;
    text-align: center;
    margin-top: 0.5rem;
  }}
  .button-primary:hover {{
    background-color: #7955c9;
  }}
  .form-container {{
    background-color: white;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }}
  .result-area {{
    background-color: white;
    border-radius: 10px;
    padding: 20px;
    margin-top: 20px;
    border: 1px solid #E2E8F0;
  }}
  @media (max-width: 768px) {{
    .feature-card {{
      margin-bottom: 1rem;
    }}
  }}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Base de conhecimento PMBOK 7
PMBOK7_KNOWLEDGE_BASE = {
    "princípios": [
        "Ser um administrador diligente, respeitoso e cuidadoso",
        "Criar um ambiente colaborativo da equipe do projeto",
        "Envolver efetivamente as partes interessadas",
        "Focar no valor",
        "Reconhecer, avaliar e responder às interações do sistema",
        "Demonstrar comportamentos de liderança",
        "Adaptar com base no contexto",
        "Incorporar qualidade nos processos e resultados",
        "Navegar na complexidade",
        "Otimizar respostas a riscos",
        "Abraçar adaptabilidade e resiliência",
        "Permitir mudança para alcançar o estado futuro previsto"
    ],
    "domínios": [
        "Stakeholders (Partes Interessadas)",
        "Team (Equipe)",
        "Development Approach and Life Cycle (Abordagem de Desenvolvimento e Ciclo de Vida)",
        "Planning (Planejamento)",
        "Project Work (Trabalho do Projeto)",
        "Delivery (Entrega)",
        "Measurement (Mensuração)",
        "Uncertainty (Incerteza)"
    ],
    "metodologias": {
        "preditiva": "Abordagem tradicional (cascata) com fases sequenciais",
        "adaptativa": "Abordagens ágeis e iterativas (Scrum, Kanban, etc.)",
        "híbrida": "Combinação de elementos preditivos e adaptativos"
    },
    "mudancas_principais": [
        "Transição de processos para princípios e domínios de performance",
        "Foco em entrega de valor em vez de apenas escopo, tempo e custo",
        "Maior ênfase em adaptabilidade e contexto",
        "Abordagem de sistemas em vez de processos isolados",
        "Reconhecimento de múltiplas abordagens (adaptativa, preditiva, híbrida)",
        "Maior ênfase na liderança e soft skills",
        "Visão holística do gerenciamento de projetos"
    ]
}

# Limites para interações
TOKEN_LIMIT = 100000
REQUEST_LIMIT = 50

# ================= INICIALIZAÇÃO DO SESSION STATE =================

if 'api_key_configured' not in st.session_state:
    st.session_state.api_key_configured = True
    if st.secrets.get("OPENAI_API_KEY"):
        st.session_state.api_key = st.secrets.get("OPENAI_API_KEY")
    else:
        st.session_state.api_key = None
        st.session_state.api_key_configured = False

if 'usage_data' not in st.session_state:
    st.session_state.usage_data = []
if 'generated_content' not in st.session_state:
    st.session_state.generated_content = ""
if 'history' not in st.session_state:
    st.session_state.history = []
if 'token_count' not in st.session_state:
    st.session_state.token_count = 0
if 'request_count' not in st.session_state:
    st.session_state.request_count = 0
if 'last_request_time' not in st.session_state:
    st.session_state.last_request_time = 0
if 'session_id' not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("%Y%m%d%H%M%S") + str(hash(datetime.now()))[:5]
if 'current_feature' not in st.session_state:
    st.session_state.current_feature = ""
if 'previous_screen' not in st.session_state:
    st.session_state.previous_screen = None

# Funcionalidades disponíveis
feature_options = {
    "Gerador de Comunicações Estruturadas": {
        "description": "Crie e-mails, relatórios e comunicados formais a partir de pontos-chave.",
        "icon": "📧",
        "color": "purple",
        "subtypes": ["E-mail Profissional", "Relatório de Status", "Comunicado Formal"]
    },
    "Assistente de Reuniões": {
        "description": "Gere agendas, atas e mensagens de follow-up para reuniões.",
        "icon": "📅",
        "color": "orange",
        "subtypes": ["Agenda de Reunião", "Ata/Resumo de Reunião", "Follow-up de Reunião"]
    },
    "Tradutor de Jargão Técnico": {
        "description": "Simplifique conteúdo técnico para diferentes públicos.",
        "icon": "🔄",
        "color": "teal",
        "subtypes": ["Simplificação de Documento Técnico", "Adaptação para Executivos", "Adaptação para Clientes", "Adaptação para Equipe Técnica"]
    },
    "Facilitador de Feedback": {
        "description": "Estruture feedback construtivo e prepare roteiros para conversas difíceis.",
        "icon": "💬",
        "color": "purple",
        "subtypes": ["Feedback de Desempenho", "Feedback sobre Entregáveis", "Roteiro para Conversa Difícil"]
    },
    "Detector de Riscos de Comunicação": {
        "description": "Analise comunicações para identificar ambiguidades e problemas potenciais.",
        "icon": "🔍",
        "color": "orange",
        "subtypes": ["Análise de E-mail", "Análise de Comunicado", "Análise de Proposta", "Análise de Documento de Requisitos"]
    },
    "Consultor PMBOK 7": {
        "description": "Oriente sobre gerenciamento de projetos conforme o PMBOK 7.",
        "icon": "📚",
        "color": "teal",
        "subtypes": ["Princípios de Gerenciamento", "Domínios de Performance", "Adaptação de Metodologias", "Ferramentas e Técnicas", "Melhores Práticas"]
    }
}

# ================= FUNÇÕES AUXILIARES =================

def header():
    """Renderiza o cabeçalho com gradiente."""
    st.markdown('<div class="header-gradient"><h1>NEXUS</h1></div>', unsafe_allow_html=True)

def sidebar():
    """Configura a barra lateral com logo e descrição."""
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-content">
            <h3>NEXUS</h3>
            <p>Assistente de Comunicação IA</p>
        </div>
        """, unsafe_allow_html=True)

def export_as_docx(content, filename="documento"):
    """Exporta o conteúdo como DOCX."""
    doc = docx.Document()
    doc.add_heading(filename, 0)
    for line in content.split("\n"):
        if line.strip() == "":
            continue
        if re.match(r'^#{1,6}\s+', line):
            header_match = re.match(r'^(#{1,6})\s+(.*)', line)
            if header_match:
                level = min(len(header_match.group(1)), 9)
                text = header_match.group(2)
                doc.add_heading(text, level)
        else:
            doc.add_paragraph(line)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def enrich_pmbok_prompt(prompt, pmbok_topic):
    """Enriquece o prompt com informações do PMBOK 7."""
    additional_info = ""
    if "Princípios" in pmbok_topic:
        additional_info += "\n\nPrincípios de Gerenciamento do PMBOK 7:\n" + "\n".join(PMBOK7_KNOWLEDGE_BASE["princípios"])
    elif "Domínios" in pmbok_topic:
        additional_info += "\n\nDomínios de Performance do PMBOK 7:\n" + "\n".join(PMBOK7_KNOWLEDGE_BASE["domínios"])
    elif "Adaptação" in pmbok_topic:
        additional_info += "\n\nAbordagens de Desenvolvimento no PMBOK 7:\n"
        for k, v in PMBOK7_KNOWLEDGE_BASE["metodologias"].items():
            additional_info += f"- {k.capitalize()}: {v}\n"
    elif "Melhores Práticas" in pmbok_topic:
        additional_info += "\n\nMudanças Principais no PMBOK 7:\n" + "\n".join([f"- {item}" for item in PMBOK7_KNOWLEDGE_BASE["mudancas_principais"]])
    return prompt + additional_info

def generate_content(prompt, model="gpt-3.5-turbo", temperature=0.7):
    """Gera conteúdo via API OpenAI."""
    if not st.session_state.api_key_configured or not st.session_state.api_key:
        return "API não configurada. Por favor, contate o administrador."
    if st.session_state.token_count >= TOKEN_LIMIT:
        return f"Você atingiu o limite de {TOKEN_LIMIT} tokens para esta sessão. Por favor, tente novamente mais tarde."
    if st.session_state.request_count >= REQUEST_LIMIT:
        return f"Você atingiu o limite de {REQUEST_LIMIT} requisições para esta sessão. Por favor, tente novamente mais tarde."
    try:
        with st.spinner("Gerando conteúdo..."):
            st.session_state.last_request_time = time.time()
            st.session_state.request_count += 1
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {st.session_state.api_key}"
            }
            system_prompt = """
            Você é o NEXUS, um assistente de IA especializado em comunicação estratégica e gerenciamento de projetos.
            Forneça respostas profissionais, estruturadas e detalhadas.
            """
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": 4000
            }
            response = requests.post("https://api.openai.com/v1/chat/completions",
                                     headers=headers,
                                     data=json.dumps(payload),
                                     timeout=60)
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                total_tokens = result['usage']['total_tokens']
                st.session_state.token_count += total_tokens
                st.session_state.usage_data.append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'feature': st.session_state.current_feature,
                    'tokens': total_tokens,
                    'model': model,
                    'session_id': st.session_state.session_id
                })
                st.session_state.history.append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'feature': st.session_state.current_feature,
                    'input': prompt[:100] + "..." if len(prompt) > 100 else prompt,
                    'output': content,
                    'model': model,
                    'session_id': st.session_state.session_id
                })
                return content
            else:
                return f"Erro na API (Status {response.status_code}): {response.text}"
    except Exception as e:
        return f"Erro ao gerar conteúdo: {str(e)}"

def feature_cards():
    """Exibe os cartões de seleção de funcionalidades."""
    st.markdown("## Selecione uma Funcionalidade")
    cols = st.columns(2)
    features_list = list(feature_options.items())
    for i, (name, details) in enumerate(features_list):
        current_col = cols[i % 2]
        with current_col:
            st.markdown(f"""
            <div class="feature-card">
                <h3 style="color: var(--dark-purple);">{details['icon']} {name}</h3>
                <p style="color: var(--text-secondary);">{details['description']}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Selecionar", key=f"select_{name}"):
                st.session_state.current_feature = name
                st.session_state.previous_screen = "home"
                st.experimental_rerun()

# ================= INTERFACE PRINCIPAL =================

def main():
    header()
    sidebar()
    
    with st.expander("ℹ️ Sobre esta versão", expanded=False):
        st.markdown(f"""
        **Versão NEXUS Aprimorada**
        - Até {REQUEST_LIMIT} requisições por sessão
        - Até {TOKEN_LIMIT} tokens por sessão
        - Design responsivo e minimalista
        - Análise avançada de tom comunicacional
        """)
    
    # Botão VOLTAR se uma funcionalidade estiver selecionada
    if st.session_state.current_feature:
        if st.button("◀️ VOLTAR", key="back_to_home"):
            st.session_state.current_feature = ""
            st.session_state.generated_content = ""
            st.experimental_rerun()
    
    # Histórico de gerações recentes
    if st.session_state.history:
        with st.expander("Histórico de Gerações Recentes", expanded=False):
            for i, item in enumerate(reversed(st.session_state.history[-5:])):
                st.markdown(f"""
                <div style="padding: 10px; border: 1px solid #E2E8F0; border-radius: 8px; margin-bottom: 10px;">
                    <strong>{item['timestamp']} - {item['feature']}</strong>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Carregar este conteúdo ↩️", key=f"load_{i}"):
                    st.session_state.current_feature = item['feature']
                    st.session_state.generated_content = item['output']
                    st.experimental_rerun()
    
    # Exibe os cartões ou a interface da funcionalidade
    if not st.session_state.current_feature:
        feature_cards()
    else:
        current_feature = st.session_state.current_feature
        details = feature_options[current_feature]
        st.markdown(f"## {details['icon']} {current_feature}")
        
        if st.session_state.token_count >= TOKEN_LIMIT:
            st.error(f"Você atingiu o limite de {TOKEN_LIMIT} tokens para esta sessão.")
        elif st.session_state.request_count >= REQUEST_LIMIT:
            st.error(f"Você atingiu o limite de {REQUEST_LIMIT} requisições para esta sessão.")
        else:
            with st.form(key=f"{current_feature}_form"):
                st.markdown('<div class="form-container">', unsafe_allow_html=True)
                st.markdown(f"<p style='font-size:1.5rem; color: var(--dark-purple);'>{details['description']}</p>", unsafe_allow_html=True)
                
                subtype = st.selectbox("Tipo de Comunicação", details['subtypes'])
                context = ""
                prompt = ""
                
                if current_feature != "Consultor PMBOK 7":
                    context = st.text_area("Contexto do Projeto", help="Descreva o projeto, fase atual e informações relevantes", height=100, placeholder="Ex: Projeto de desenvolvimento de aplicativo móvel, fase de testes")
                
                # Montagem do prompt com base na funcionalidade selecionada
                if current_feature == "Gerador de Comunicações Estruturadas":
                    audience = st.text_input("Público-alvo", help="Para quem será enviada a comunicação", placeholder="Ex: Cliente, equipe, stakeholder")
                    key_points = st.text_area("Pontos-chave", help="Liste os principais pontos da comunicação", height=150, placeholder="Ex: Atraso de 3 dias; plano de recuperação")
                    tone = st.select_slider("Tom da Comunicação", options=["Muito Formal", "Formal", "Neutro", "Amigável", "Casual"], value="Neutro")
                    prompt = f"""
                    Gere um {subtype} com base nas seguintes informações:
                    
                    Contexto do Projeto: {context}
                    Público-alvo: {audience}
                    Pontos-chave: {key_points}
                    Tom desejado: {tone}
                    
                    Formate a saída adequadamente para um {subtype}.
                    """
                elif current_feature == "Assistente de Reuniões":
                    participants = st.text_area("Participantes", help="Liste os participantes e suas funções", height=100, placeholder="Ex: João Silva (Gerente), Maria Costa (Desenvolvedora)")
                    topics = st.text_area("Tópicos a serem abordados", help="Liste os tópicos da reunião", height=150, placeholder="Ex: Atualização do cronograma, bugs, feedback do cliente")
                    duration = st.number_input("Duração (minutos)", min_value=15, max_value=240, value=60, step=15)
                    if subtype == "Agenda de Reunião":
                        prompt = f"""
                        Crie uma agenda para uma reunião de {duration} minutos com base nas informações:
                        
                        Contexto do Projeto: {context}
                        Participantes: {participants}
                        Tópicos: {topics}
                        """
                    elif subtype == "Ata/Resumo de Reunião":
                        decisions = st.text_area("Decisões tomadas", help="Liste as decisões da reunião", height=100, placeholder="Ex: Aprovação do novo design")
                        actions = st.text_area("Ações acordadas", help="Liste as ações acordadas, responsáveis e prazos", height=100, placeholder="Ex: João: correção de bug até amanhã")
                        prompt = f"""
                        Crie uma ata/resumo para uma reunião de {duration} minutos com base nas informações:
                        
                        Contexto do Projeto: {context}
                        Participantes: {participants}
                        Tópicos: {topics}
                        Decisões: {decisions}
                        Ações: {actions}
                        """
                    else:  # Follow-up
                        meeting_outcome = st.text_area("Resultado da reunião", help="Resuma os resultados da reunião", height=100, placeholder="Ex: Definição de prioridades para o próximo sprint")
                        action_items = st.text_area("Itens de ação", help="Liste os itens de ação", height=100, placeholder="Ex: João: revisão de código; Maria: implementação da nova feature")
                        prompt = f"""
                        Crie uma mensagem de follow-up para uma reunião com base nas informações:
                        
                        Contexto do Projeto: {context}
                        Participantes: {participants}
                        Tópicos: {topics}
                        Resultado: {meeting_outcome}
                        Itens de ação: {action_items}
                        """
                elif current_feature == "Tradutor de Jargão Técnico":
                    technical_content = st.text_area("Conteúdo Técnico", help="Cole o texto técnico a ser adaptado", height=200, placeholder="Ex: Implementação do Redux com reducers imutáveis...")
                    audience = st.selectbox("Público-alvo", ["Executivos", "Clientes não-técnicos", "Equipe de Negócios", "Equipe Técnica Junior"])
                    key_concepts = st.text_input("Conceitos-chave", help="Liste os conceitos que devem ser mantidos", placeholder="Ex: gerenciamento de estado, API")
                    prompt = f"""
                    Adapte o seguinte conteúdo técnico para um público de {audience}:
                    
                    Contexto do Projeto: {context}
                    Conteúdo Original: {technical_content}
                    Conceitos-chave: {key_concepts}
                    """
                elif current_feature == "Facilitador de Feedback":
                    situation = st.text_area("Situação", help="Descreva a situação para o feedback", height=150, placeholder="Ex: Atraso na entrega")
                    strengths = st.text_area("Pontos Fortes", help="Liste os pontos positivos", height=100, placeholder="Ex: Qualidade do código")
                    areas = st.text_area("Áreas para Melhoria", help="Liste os pontos a melhorar", height=100, placeholder="Ex: Falta de comunicação")
                    relationship = st.selectbox("Relação com o Receptor", ["Membro da equipe", "Colega", "Superior", "Cliente", "Fornecedor"])
                    prompt = f"""
                    Estruture um {subtype} de feedback com base nas informações:
                    
                    Contexto do Projeto: {context}
                    Situação: {situation}
                    Pontos Fortes: {strengths}
                    Áreas para Melhoria: {areas}
                    Relação: {relationship}
                    """
                elif current_feature == "Detector de Riscos de Comunicação":
                    content_to_analyze = st.text_area("Conteúdo para Análise", help="Cole o conteúdo a ser analisado", height=200, placeholder="Ex: Comunicação com possíveis ambiguidades...")
                    audience = st.text_input("Público-alvo", help="Quem receberá a comunicação", placeholder="Ex: Cliente executivo")
                    stakes = st.select_slider("Importância", options=["Baixa", "Média", "Alta", "Crítica"], value="Média")
                    prompt = f"""
                    Analise o seguinte {subtype} quanto a riscos de comunicação:
                    
                    Contexto do Projeto: {context}
                    Público-alvo: {audience}
                    Importância: {stakes}
                    
                    Conteúdo:
                    {content_to_analyze}
                    """
                elif current_feature == "Consultor PMBOK 7":
                    pmbok_topic = subtype
                    project_context = st.text_area("Contexto do Projeto", help="Descreva o contexto do projeto", height=100, placeholder="Ex: Projeto de software com metodologia híbrida")
                    specific_question = st.text_area("Sua Dúvida", help="Detalhe sua dúvida sobre o PMBOK 7", height=150, placeholder="Ex: Como aplicar os princípios de valor do PMBOK 7?")
                    experience_level = st.select_slider("Nível de Experiência", options=["Iniciante", "Intermediário", "Avançado", "Especialista"], value="Intermediário")
                    organization_context = st.text_input("Contexto Organizacional", help="Descreva o contexto organizacional (opcional)", placeholder="Ex: Empresa de médio porte")
                    base_prompt = f"""
                    Forneça uma orientação detalhada sobre "{pmbok_topic}" do PMBOK 7 com base nas informações:
                    
                    Contexto do Projeto: {project_context}
                    Dúvida: {specific_question}
                    Nível de Experiência: {experience_level}
                    Contexto Organizacional: {organization_context}
                    """
                    prompt = enrich_pmbok_prompt(base_prompt, pmbok_topic)
                
                st.markdown('</div>', unsafe_allow_html=True)
                submit_button = st.form_submit_button("GERAR", type="primary")
            
            if submit_button:
                if not st.session_state.api_key_configured:
                    st.error("API não configurada. Por favor, contate o administrador.")
                elif st.session_state.token_count >= TOKEN_LIMIT:
                    st.error(f"Limite de {TOKEN_LIMIT} tokens atingido.")
                elif st.session_state.request_count >= REQUEST_LIMIT:
                    st.error(f"Limite de {REQUEST_LIMIT} requisições atingido.")
                else:
                    generated = generate_content(prompt)
                    st.session_state.generated_content = generated
                    st.markdown("### Resultado")
                    st.markdown(f'<div class="result-area">{generated}</div>', unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label="📄 Baixar como TXT",
                            data=generated,
                            file_name=f"{current_feature.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain"
                        )
                    with col2:
                        docx_buffer = export_as_docx(generated)
                        st.download_button(
                            label="📝 Baixar como DOCX",
                            data=docx_buffer,
                            file_name=f"{current_feature.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                    if st.button("◀️ VOLTAR", key="back_from_result"):
                        st.session_state.generated_content = ""
                        st.experimental_rerun()

if __name__ == "__main__":
    main()
