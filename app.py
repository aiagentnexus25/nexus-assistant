import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import os
import re
import docx
from io import BytesIO
import time
import hashlib

# ================= CONFIGURATION =================

# Configuração da página
st.set_page_config(
    page_title="NEXUS - Assistente de Comunicação de Projetos",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #3B82F6;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-card {
        background-color: #F3F4F6;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        border-left: 5px solid #3B82F6;
    }
    .result-area {
        background-color: #F0F9FF;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
        border: 1px solid #BAE6FD;
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
    .feedback-good {
        color: #059669;
        font-weight: bold;
    }
    .feedback-bad {
        color: #DC2626;
        font-weight: bold;
    }
    .stAlert {
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .usage-info {
        background-color: #EFF6FF;
        border-radius: 8px;
        padding: 10px;
        margin: 10px 0;
        border: 1px solid #DBEAFE;
    }
    .export-options {
        background-color: #F8F9FA;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid #E9ECEF;
    }
    .template-card {
        background-color: #F0FDF4;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        border: 1px solid #DCFCE7;
    }
    .model-selector {
        background-color: #F5F3FF;
        border-radius: 8px;
        padding: 12px;
        margin: 10px 0;
        border: 1px solid #EDE9FE;
    }
    .history-item {
        background-color: #FAFAFA;
        border-radius: 8px;
        padding: 10px;
        margin: 8px 0;
        border-left: 3px solid #3B82F6;
    }
</style>
""", unsafe_allow_html=True)

# ================= CONSTANTS =================

# Limites de uso restritivos para testes
TOKEN_LIMIT = 3000      # Limite total de tokens por sessão
REQUEST_LIMIT = 5       # Limite de solicitações por sessão
RATE_LIMIT_SECONDS = 60 # Tempo mínimo (em segundos) entre requisições

# System prompt base para o assistente
system_prompt = """
Você é o NEXUS, um assistente especializado em comunicação de projetos. Seu objetivo é ajudar gerentes de projetos, líderes de equipe e outros profissionais a comunicar-se de forma clara, eficaz e profissional em diversos contextos de projetos.

Você possui cinco habilidades principais:

1. Gerador de Comunicações Estruturadas: Criar e-mails profissionais, relatórios de status e comunicados formais.
2. Assistente de Reuniões: Gerar agendas detalhadas, atas e resumos de reuniões, e estruturar follow-ups.
3. Tradutor de Jargão Técnico: Simplificar linguagem técnica, adaptar comunicações para diferentes públicos e traduzir requisitos técnicos.
4. Facilitador de Feedback: Estruturar feedback construtivo, transformar críticas em sugestões e criar roteiros para conversas difíceis.
5. Detector de Riscos de Comunicação: Analisar comunicações, sugerir alternativas mais claras e avaliar adequação ao público.

Ao responder, você deve:
- Ser conciso mas completo
- Usar linguagem profissional e tom adequado para o contexto
- Estruturar o conteúdo de forma lógica e clara
- Focar em comunicação eficaz e construtiva
- Evitar jargões desnecessários, a menos que sejam apropriados para o público-alvo

Observação importante: Esta é uma versão de demonstração com limites de uso. Seja eficiente e direto em suas respostas.
"""

# Definição de funcionalidades disponíveis
feature_options = {
    "Gerador de Comunicações Estruturadas": {
        "description": "Crie e-mails profissionais, relatórios de status e comunicados formais a partir de pontos-chave.",
        "icon": "📧",
        "subtypes": ["E-mail Profissional", "Relatório de Status", "Comunicado Formal"]
    },
    "Assistente de Reuniões": {
        "description": "Gere agendas detalhadas, atas de reuniões e mensagens de follow-up estruturadas.",
        "icon": "📅",
        "subtypes": ["Agenda de Reunião", "Ata/Resumo de Reunião", "Follow-up de Reunião"]
    },
    "Tradutor de Jargão Técnico": {
        "description": "Simplifique linguagem técnica e adapte comunicações para diferentes públicos.",
        "icon": "🔄",
        "subtypes": ["Simplificação de Documento Técnico", "Adaptação para Executivos", "Adaptação para Clientes", "Adaptação para Equipe Técnica"]
    },
    "Facilitador de Feedback": {
        "description": "Estruture feedback construtivo e prepare roteiros para conversas difíceis.",
        "icon": "💬",
        "subtypes": ["Feedback de Desempenho", "Feedback sobre Entregáveis", "Roteiro para Conversa Difícil"]
    },
    "Detector de Riscos de Comunicação": {
        "description": "Analise comunicações para identificar ambiguidades e problemas potenciais.",
        "icon": "🔍",
        "subtypes": ["Análise de E-mail", "Análise de Comunicado", "Análise de Proposta", "Análise de Documento de Requisitos"]
    }
}

# ================= SISTEMA DE CACHE PARA API OPENAI =================

class OpenAICache:
    def __init__(self, cache_dir="cache", ttl_hours=24):
        """
        Inicializa o sistema de cache
        
        Args:
            cache_dir (str): Diretório para armazenar os arquivos de cache
            ttl_hours (int): Tempo de vida do cache em horas
        """
        self.cache_dir = cache_dir
        self.ttl_hours = ttl_hours
        
        # Criar diretório de cache se não existir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def get_cache_key(self, prompt, model, temperature):
        """
        Gera uma chave única para o cache baseado nos parâmetros da solicitação
        
        Args:
            prompt (str): O prompt enviado para a API
            model (str): O modelo usado (ex: gpt-3.5-turbo)
            temperature (float): A temperatura usada para geração
            
        Returns:
            str: Chave hash única para o cache
        """
        # Criar string com todos os parâmetros relevantes
        cache_str = f"{prompt}|{model}|{temperature}"
        
        # Gerar hash MD5 para usar como nome de arquivo
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def get_from_cache(self, prompt, model, temperature):
        """
        Tenta recuperar uma resposta do cache
        
        Args:
            prompt (str): O prompt enviado para a API
            model (str): O modelo usado (ex: gpt-3.5-turbo)
            temperature (float): A temperatura usada para geração
            
        Returns:
            dict or None: Dados do cache se disponível e válido, ou None
        """
        cache_key = self.get_cache_key(prompt, model, temperature)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        # Verificar se arquivo de cache existe
        if not os.path.exists(cache_file):
            return None

# ================= SIDEBAR =================

# Sidebar para configuração
def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        st.image("https://via.placeholder.com/150x150.png?text=NEXUS", width=150)
        
        # Mostrar status da API
        st.markdown("### Status")
        if st.session_state.api_key_configured:
            st.success("✅ API configurada automaticamente")
        else:
            st.error("❌ API não configurada. Contate o administrador.")
        
        # Seletor de modelo
        st.markdown("### Configurações")
        model_selector()
        
        # Exibir estatísticas de uso
        st.markdown("### Seu Uso")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Requisições", f"{st.session_state.request_count}/{REQUEST_LIMIT}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Tokens", f"{st.session_state.token_count}/{TOKEN_LIMIT}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Barras de progresso
        st.progress(st.session_state.request_count / REQUEST_LIMIT)
        st.caption("Uso de requisições")
        
        st.progress(st.session_state.token_count / TOKEN_LIMIT)
        st.caption("Uso de tokens")
        
        # Informações sobre cache
        if st.session_state.usage_data:
            cache_hits = sum(1 for item in st.session_state.usage_data if 'from_cache' in item and item['from_cache'])
            total_requests = len(st.session_state.usage_data)
            
            if total_requests > 0:
                cache_hit_rate = (cache_hits / total_requests) * 100
                st.markdown('<div class="usage-info">', unsafe_allow_html=True)
                st.caption(f"Taxa de cache: {cache_hit_rate:.1f}%")
                if cache_hits > 0:
                    tokens_saved = sum(item['tokens'] for item in st.session_state.usage_data if 'from_cache' in item and item['from_cache'])
                    st.caption(f"Tokens economizados: {tokens_saved}")
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Informações de sessão (apenas para rastreamento)
        st.markdown('<div class="usage-info">', unsafe_allow_html=True)
        st.caption(f"ID da sessão: {st.session_state.session_id}")
        st.caption(f"Início: {datetime.fromtimestamp(st.session_state.last_request_time).strftime('%H:%M:%S') if st.session_state.last_request_time > 0 else 'N/A'}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Feedback
        st.markdown("### Feedback")
        feedback = st.radio("Como está sua experiência?", ["😀 Excelente", "🙂 Boa", "😐 Neutra", "🙁 Ruim", "😞 Péssima"])
        feedback_text = st.text_area("Comentários adicionais")
        
        if st.button("Enviar Feedback"):
            st.success("Feedback enviado. Obrigado por nos ajudar a melhorar!")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Informação sobre limites de uso
        st.markdown("---")
        st.caption("Esta é uma versão de demonstração com limites de uso para controlar custos. Para uso sem limites, implemente o NEXUS em seu próprio ambiente.")

# ================= MAIN INTERFACE =================

def main():
    # Renderizar a barra lateral
    render_sidebar()
    
    # Interface principal
    st.markdown('<h1 class="main-header">NEXUS</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Comunicação de projetos clara, eficaz e profissional</p>', unsafe_allow_html=True)
    
    # Mensagem sobre versão de teste
    st.info(f"""
    **Versão de Demonstração**
    Esta é uma versão de demonstração do NEXUS com limites de uso:
    - Máximo de {REQUEST_LIMIT} requisições por sessão
    - Máximo de {TOKEN_LIMIT} tokens por sessão
    - Tempo mínimo de {RATE_LIMIT_SECONDS} segundos entre requisições
    """)
    
    # Histórico de gerações recentes
    render_history_panel()
    
    # Seleção de funcionalidade
    # Organizar opções em colunas
    col1, col2 = st.columns(2)
    
    count = 0
    for feature, details in feature_options.items():
        if count % 2 == 0:
            with col1:
                with st.expander(f"{details['icon']} {feature}", expanded=False):
                    st.markdown(f"**{details['description']}**")
                    if st.button(f"Usar {feature}", key=f"select_{feature}"):
                        st.session_state.current_feature = feature
                        st.experimental_rerun()
        else:
            with col2:
                with st.expander(f"{details['icon']} {feature}", expanded=False):
                    st.markdown(f"**{details['description']}**")
                    if st.button(f"Usar {feature}", key=f"select_{feature}"):
                        st.session_state.current_feature = feature
                        st.experimental_rerun()
        count += 1
    
    # ================= FEATURE INTERFACE =================
    
    # Se uma funcionalidade foi selecionada na sessão atual ou anteriormente
    if st.session_state.current_feature:
        current_feature = st.session_state.current_feature
        feature_details = feature_options[current_feature]
        
        st.markdown(f"## {feature_details['icon']} {current_feature}")
        
        # Verificar limites antes de mostrar a interface
        if st.session_state.token_count >= TOKEN_LIMIT:
            st.error(f"Você atingiu o limite de {TOKEN_LIMIT} tokens para esta sessão. Por favor, tente novamente mais tarde.")
        elif st.session_state.request_count >= REQUEST_LIMIT:
            st.error(f"Você atingiu o limite de {REQUEST_LIMIT} requisições para esta sessão. Por favor, tente novamente mais tarde.")
        elif time.time() - st.session_state.last_request_time < RATE_LIMIT_SECONDS and st.session_state.request_count > 0:
            wait_time = round(RATE_LIMIT_SECONDS - (time.time() - st.session_state.last_request_time))
            st.warning(f"Por favor, aguarde {wait_time} segundos antes de fazer outra requisição.")
        else:
            # Verificar templates disponíveis
            selected_template = template_selector(current_feature)
            template_data = None
            
            if selected_template:
                template_data = selected_template['template']
            
            # Interface específica da funcionalidade
            with st.form(key=f"{current_feature}_form"):
                st.markdown(f"**{feature_details['description']}**")
                
                # Campo de subtipo
                subtype = st.selectbox("Tipo de Comunicação", feature_details['subtypes'])
                
                # Campos comuns a todas as funcionalidades
                context = st.text_area("Contexto do Projeto", 
                                    help="Descreva o projeto, fase atual e informações relevantes",
                                    height=100,
                                    placeholder="Ex: Projeto de desenvolvimento do aplicativo mobile, fase de testes",
                                    value=template_data.get('context', "") if template_data else "")
                
                # Campos específicos por funcionalidade
                prompt = ""
                
                if current_feature == "Gerador de Comunicações Estruturadas":
                    audience = st.text_input("Público-alvo", 
                                        help="Para quem esta comunicação será enviada (equipe, cliente, stakeholder)",
                                        placeholder="Ex: Cliente, diretor de marketing da empresa XYZ",
                                        value=template_data.get('audience', "") if template_data else "")
                    key_points = st.text_area("Pontos-chave", 
                                            help="Liste os principais pontos que devem ser incluídos na comunicação",
                                            height=150,
                                            placeholder="Ex: Atraso de 3 dias devido a bugs na integração; Plano de recuperação com recursos adicionais",
                                            value=template_data.get('key_points', "") if template_data else "")
                    tone = st.select_slider("Tom da Comunicação", 
                                        options=["Muito Formal", "Formal", "Neutro", "Amigável", "Casual"],
                                        value=template_data.get('tone', "Neutro") if template_data else "Neutro")
                    
                    prompt = f"""
                    Gere um {subtype} com base nas seguintes informações:
                    
                    Contexto do Projeto: {context}
                    Público-alvo: {audience}
                    Pontos-chave: {key_points}
                    Tom desejado: {tone}
                    
                    Formate a saída adequadamente para um {subtype}, incluindo assunto/título e estrutura apropriada.
                    """
                    
                elif current_feature == "Assistente de Reuniões":
                    participants = st.text_area("Participantes", 
                                            help="Liste os participantes e suas funções",
                                            height=100,
                                            placeholder="Ex: João Silva (Gerente de Projeto), Maria Costa (Desenvolvedora Frontend)",
                                            value=template_data.get('participants', "") if template_data else "")
                    topics = st.text_area("Tópicos a serem abordados", 
                                        help="Liste os tópicos que precisam ser discutidos",
                                        height=150,
                                        placeholder="Ex: Atualização do cronograma, Bugs pendentes, Feedback do cliente",
                                        value=template_data.get('topics', "") if template_data else "")
                    duration = st.number_input("Duração (minutos)", 
                                           min_value=15, 
                                           max_value=240, 
                                           value=template_data.get('duration', 60) if template_data and 'duration' in template_data else 60, 
                                           step=15)
                    
                    if subtype == "Agenda de Reunião":
                        prompt = f"""
                        Crie uma agenda detalhada para uma reunião de {duration} minutos com base nas seguintes informações:
                        
                        Contexto do Projeto: {context}
                        Participantes: {participants}
                        Tópicos a serem abordados: {topics}
                        
                        Inclua alocação de tempo para cada item, responsáveis e objetivos claros.
                        """
                    elif subtype == "Ata/Resumo de Reunião":
                        decisions = st.text_area("Decisões tomadas", 
                                            help="Liste as principais decisões tomadas durante a reunião",
                                            height=100,
                                            placeholder="Ex: Aprovação do novo design, Extensão do prazo em 1 semana",
                                            value=template_data.get('decisions', "") if template_data else "")
                        actions = st.text_area("Ações acordadas", 
                                           help="Liste as ações acordadas, responsáveis e prazos",
                                           height=100,
                                           placeholder="Ex: João irá corrigir o bug #123 até amanhã, Maria criará novos componentes até sexta",
                                           value=template_data.get('actions', "") if template_data else "")
                        
                        prompt = f"""
                        Crie uma ata/resumo detalhado para uma reunião de {duration} minutos com base nas seguintes informações:
                        
                        Contexto do Projeto: {context}
                        Participantes: {participants}
                        Tópicos abordados: {topics}
                        Decisões tomadas: {decisions}
                        Ações acordadas: {actions}
                        
                        Organize por tópicos, destacando claramente decisões e próximos passos com responsáveis.
                        """
                    else:  # Follow-up
                        meeting_outcome = st.text_area("Resultado da reunião", 
                                                   help="Resuma os principais resultados da reunião",
                                                   height=100,
                                                   placeholder="Ex: Definidas as prioridades para o próximo sprint e resolvidos os bloqueios atuais",
                                                   value=template_data.get('meeting_outcome', "") if template_data else "")
                        action_items = st.text_area("Itens de ação", 
                                                help="Liste os itens de ação, responsáveis e prazos",
                                                height=100,
                                                placeholder="Ex: João: revisão de código até 25/03; Maria: implementação da nova feature até 27/03",
                                                value=template_data.get('action_items', "") if template_data else "")
                        
                        prompt = f"""
                        Crie uma mensagem de follow-up para uma reunião com base nas seguintes informações:
                        
                        Contexto do Projeto: {context}
                        Participantes: {participants}
                        Tópicos abordados: {topics}
                        Resultado da reunião: {meeting_outcome}
                        Itens de ação: {action_items}
                        
                        A mensagem deve agradecer a participação, resumir os principais pontos, detalhar próximos passos
                        com responsáveis e prazos, e solicitar confirmação/feedback conforme apropriado.
                        """
                        
                elif current_feature == "Tradutor de Jargão Técnico":
                    technical_content = st.text_area("Conteúdo Técnico", 
                                                help="Cole aqui o texto técnico que precisa ser traduzido",
                                                height=200,
                                                placeholder="Ex: A implementação do Redux utiliza reducers imutáveis para gerenciar o estado global da aplicação...",
                                                value=template_data.get('technical_content', "") if template_data else "")
                    audience = st.selectbox("Público-alvo", 
                                        ["Executivos", "Clientes não-técnicos", "Equipe de Negócios", "Equipe Técnica Junior"],
                                        index=["Executivos", "Clientes não-técnicos", "Equipe de Negócios", "Equipe Técnica Junior"].index(template_data.get('audience', "Executivos")) if template_data and 'audience' in template_data else 0)
                    key_concepts = st.text_input("Conceitos-chave a preservar", 
                                            help="Liste conceitos técnicos que devem ser mantidos mesmo se simplificados",
                                            placeholder="Ex: gerenciamento de estado, API, front-end",
                                            value=template_data.get('key_concepts', "") if template_data else "")
                    
                    prompt = f"""
                    Traduza/adapte o seguinte conteúdo técnico para um público de {audience} com base nas seguintes informações:
                    
                    Contexto do Projeto: {context}
                    Conteúdo Técnico Original: {technical_content}
                    Conceitos-chave a preservar: {key_concepts}
                    
                    Para {audience}, foque em: 
                    - {'Impacto nos negócios e resultados de alto nível' if audience == 'Executivos' else ''}
                    - {'Benefícios e funcionalidades em linguagem acessível' if audience == 'Clientes não-técnicos' else ''}
                    - {'Conexão com objetivos de negócios e processos' if audience == 'Equipe de Negócios' else ''}
                    - {'Explicações técnicas mais detalhadas, mas com conceitos explicados' if audience == 'Equipe Técnica Junior' else ''}
                    
                    Mantenha a precisão conceitual mesmo simplificando a linguagem.
                    """
                    
                elif current_feature == "Facilitador de Feedback":
                    situation = st.text_area("Situação", 
                                        help="Descreva a situação específica para a qual você precisa fornecer feedback",
                                        height=150,
                                        placeholder="Ex: Atraso na entrega de componentes para o projeto principal...",
                                        value=template_data.get('situation', "") if template_data else "")
                    strengths = st.text_area("Pontos Fortes", 
                                        help="Liste aspectos positivos que devem ser destacados",
                                        height=100,
                                        placeholder="Ex: Qualidade do código entregue, comunicação proativa de desafios",
                                        value=template_data.get('strengths', "") if template_data else "")
                    areas_for_improvement = st.text_area("Áreas para Melhoria", 
                                                    help="Liste aspectos que precisam ser melhorados",
                                                    height=100,
                                                    placeholder="Ex: Estimativas de tempo irrealistas, falha em pedir ajuda quando bloqueado",
                                                    value=template_data.get('areas_for_improvement', "") if template_data else "")
                    relationship = st.selectbox("Relação com o Receptor", 
                                            ["Membro da equipe direto", "Colega de mesmo nível", "Superior hierárquico", "Cliente", "Fornecedor"],
                                            index=["Membro da equipe direto", "Colega de mesmo nível", "Superior hierárquico", "Cliente", "Fornecedor"].index(template_data.get('relationship', "Membro da equipe direto")) if template_data and 'relationship' in template_data else 0)
                    
                    prompt = f"""
                    Estruture um {subtype} construtivo e eficaz com base nas seguintes informações:
                    
                    Contexto do Projeto: {context}
                    Situação específica: {situation}
                    Pontos fortes a destacar: {strengths}
                    Áreas para melhoria: {areas_for_improvement}
                    Relação com o receptor: {relationship}
                    
                    O feedback deve:
                    - Ser específico e baseado em comportamentos observáveis
                    - Equilibrar aspectos positivos e áreas de melhoria
                    - Incluir exemplos concretos
                    - Oferecer sugestões acionáveis
                    - Usar tom apropriado para a relação ({relationship})
                    - Focar em crescimento e desenvolvimento, não em crítica
                    
                    Formate como um roteiro/script que o usuário pode seguir na conversa ou adaptar para uma comunicação escrita.
                    """
                    
                elif current_feature == "Detector de Riscos de Comunicação":
                    content_to_analyze = st.text_area("Conteúdo para Análise", 
                                                  help="Cole aqui o texto que você deseja analisar quanto a riscos de comunicação",
                                                  height=200,
                                                  placeholder="Ex: Devido a circunstâncias imprevistas no desenvolvimento, alguns recursos podem sofrer atrasos...",
                                                  value=template_data.get('content_to_analyze', "") if template_data else "")
                    audience = st.text_input("Público-alvo", 
                                        help="Descreva quem receberá esta comunicação",
                                        placeholder="Ex: Cliente executivo com pouco conhecimento técnico",
                                        value=template_data.get('audience', "") if template_data else "")
                    stakes = st.select_slider("Importância da Comunicação", 
                                          options=["Baixa", "Média", "Alta", "Crítica"],
                                          value=template_data.get('stakes', "Média") if template_data else "Média")
                    
                    prompt = f"""
                    Analise o seguinte {subtype} quanto a riscos de comunicação:
                    
                    Contexto do Projeto: {context}
                    Público-alvo: {audience}
                    Importância da comunicação: {stakes}
                    
                    Conteúdo para análise:
                    ---
                    {content_to_analyze}
                    ---
                    
                    Sua análise deve:
                    1. Identificar ambiguidades, informações incompletas ou confusas
                    2. Apontar possíveis mal-entendidos baseados no público-alvo
                    3. Detectar problemas de tom ou linguagem inapropriada
                    4. Identificar informações sensíveis ou potencialmente problemáticas
                    5. Sugerir reformulações específicas para cada problema identificado
                    
                    Organize sua análise em forma de tabela com colunas para: Trecho problemático, Risco potencial, Sugestão de melhoria.
                    Ao final, forneça uma avaliação geral dos riscos de comunicação (Baixo/Médio/Alto) e um resumo das principais recomendações.
                    """
                
                # Usar o modelo selecionado na barra lateral
                model = st.session_state.model_choice
                model_info = ""
                
                if model == "gpt-3.5-turbo":
                    model_info = "Usando GPT-3.5 Turbo (mais rápido)"
                else:
                    model_info = "Usando GPT-4 (mais capaz, maior consumo)"
                
                st.caption(model_info)
                
                submit_button = st.form_submit_button(f"Gerar {current_feature}")
            
            if submit_button:
                if not st.session_state.api_key_configured:
                    st.error("API não configurada. Por favor, contate o administrador.")
                elif st.session_state.token_count >= TOKEN_LIMIT:
                    st.error(f"Você atingiu o limite de {TOKEN_LIMIT} tokens para esta sessão. Por favor, tente novamente mais tarde.")
                elif st.session_state.request_count >= REQUEST_LIMIT:
                    st.error(f"Você atingiu o limite de {REQUEST_LIMIT} requisições para esta sessão. Por favor, tente novamente mais tarde.")
                elif time.time() - st.session_state.last_request_time < RATE_LIMIT_SECONDS and st.session_state.request_count > 0:
                    wait_time = round(RATE_LIMIT_SECONDS - (time.time() - st.session_state.last_request_time))
                    st.warning(f"Por favor, aguarde {wait_time} segundos antes de fazer outra requisição.")
                else:
                    # Gerar conteúdo usando o modelo selecionado
                    generated_content = generate_content(prompt, model=model, temperature=0.7)
                    st.session_state.generated_content = generated_content
                    
                    # Exibir resultado
                    st.markdown("### Resultado")
                    st.markdown('<div class="result-area">', unsafe_allow_html=True)
                    st.markdown(generated_content)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Opções de exportação aprimoradas
                    enhanced_export_options(generated_content, current_feature)
                    
                    # Feedback sobre o resultado
                    st.markdown("### Este resultado foi útil?")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("👍 Sim, foi útil"):
                            st.markdown('<p class="feedback-good">Obrigado pelo feedback positivo!</p>', unsafe_allow_html=True)
                    
                    with col2:
                        if st.button("👎 Não, preciso de melhoria"):
                            st.markdown('<p class="feedback-bad">Lamentamos que não tenha atendido suas expectativas. Por favor, forneça detalhes no campo de feedback na barra lateral para podermos melhorar.</p>', unsafe_allow_html=True)
    
    # ================= FOOTER =================
    
    # Nota para o artigo
    st.write("")
    st.write("")
    st.markdown("""
    ---
    ### Sobre esta demonstração do NEXUS
    
    Este aplicativo é uma versão de demonstração do NEXUS, um assistente de IA para comunicação de projetos. Foi criado como parte do artigo "**Comunicação eficiente em projetos: como a IA pode ajudar gerentes e equipes**".
    
    Para implementar o NEXUS em seu próprio ambiente:
    1. Acesse o código-fonte no GitHub: [github.com/seu-usuario/nexus-assistant](https://github.com/seu-usuario/nexus-assistant)
    2. Siga as instruções de instalação no README
    3. Configure com sua própria chave API da OpenAI
    4. Personalize para as necessidades específicas da sua equipe
    
    **Experimente as cinco funcionalidades principais do NEXUS e veja como a IA pode transformar a comunicação nos seus projetos!**
    """)
    
    # Rodapé com créditos
    st.markdown("""
    <div style="text-align: center; color: gray; font-size: 0.8rem;">
        NEXUS | Assistente de Comunicação de Projetos | © 2025
    </div>
    """, unsafe_allow_html=True)

# Executar o aplicativo
if __name__ == "__main__":
    main()
        
        try:
            # Carregar dados do cache
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Verificar TTL (Time To Live)
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            if cache_time + timedelta(hours=self.ttl_hours) < datetime.now():
                # Cache expirado
                return None
            
            return cache_data
        except Exception as e:
            # Em caso de erro, ignorar o cache
            print(f"Erro ao ler cache: {str(e)}")
            return None
    
    def save_to_cache(self, prompt, model, temperature, response_data):
        """
        Salva uma resposta da API no cache
        
        Args:
            prompt (str): O prompt enviado para a API
            model (str): O modelo usado (ex: gpt-3.5-turbo)
            temperature (float): A temperatura usada para geração
            response_data (dict): Dados da resposta da API
        """
        cache_key = self.get_cache_key(prompt, model, temperature)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        # Preparar dados para cache
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'prompt': prompt,
            'model': model,
            'temperature': temperature,
            'response': response_data
        }
        
        try:
            # Salvar no cache
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao salvar cache: {str(e)}")

# ================= BIBLIOTECA DE TEMPLATES PRÉ-CONFIGURADOS =================

# Estrutura de templates pré-configurados
template_library = {
    "Gerador de Comunicações Estruturadas": {
        "E-mail de Atraso de Projeto": {
            "description": "E-mail para comunicar atraso em cronograma de projeto",
            "template": {
                "context": "Projeto {nome_projeto}, fase de {fase_atual}",
                "audience": "Cliente, {cargo_cliente} da empresa {nome_empresa}",
                "key_points": "Atraso de {dias} dias devido a {motivo}; Plano de recuperação com {solucao}; Impacto {impacto} no prazo final",
                "tone": "Formal"
            },
            "prompt_template": """
            Gere um E-mail Profissional para comunicar um atraso de projeto com base nas seguintes informações:
            
            Contexto do Projeto: Projeto {nome_projeto}, fase de {fase_atual}
            Público-alvo: Cliente, {cargo_cliente} da empresa {nome_empresa}
            Pontos-chave: 
            - Atraso de {dias} dias devido a {motivo}
            - Plano de recuperação com {solucao}
            - Impacto {impacto} no prazo final
            Tom desejado: Formal
            
            O e-mail deve ser transparente sobre o problema, mas focado em soluções e próximos passos.
            Inclua um assunto claro, saudação apropriada, corpo estruturado e fechamento profissional.
            """
        },
        "Relatório de Status Semanal": {
            "description": "Relatório padrão de status semanal de projeto",
            "template": {
                "context": "Projeto {nome_projeto}, semana {numero_semana}",
                "audience": "Equipe e stakeholders",
                "key_points": "Progresso: {progresso}; Próximos passos: {proximos_passos}; Riscos: {riscos}; Bloqueios: {bloqueios}",
                "tone": "Neutro"
            },
            "prompt_template": """
            Gere um Relatório de Status detalhado para a semana com base nas seguintes informações:
            
            Contexto do Projeto: Projeto {nome_projeto}, semana {numero_semana}
            Público-alvo: Equipe e stakeholders
            Pontos-chave:
            - Progresso da semana: {progresso}
            - Próximos passos: {proximos_passos}
            - Riscos identificados: {riscos}
            - Bloqueios atuais: {bloqueios}
            Tom desejado: Neutro
            
            O relatório deve ser conciso mas informativo, organizado por seções claras, e incluir um resumo executivo no início.
            Use marcadores para facilitar a leitura rápida de informações importantes.
            """
        },
        "Comunicado de Mudança de Escopo": {
            "description": "Comunicado formal sobre mudança de escopo de projeto",
            "template": {
                "context": "Projeto {nome_projeto}, fase de {fase_atual}",
                "audience": "Todos os stakeholders",
                "key_points": "Mudança nos requisitos {requisitos}; Impacto em {impacto}; Ajustes necessários: {ajustes}",
                "tone": "Formal"
            },
            "prompt_template": """
            Gere um Comunicado Formal sobre mudança de escopo com base nas seguintes informações:
            
            Contexto do Projeto: Projeto {nome_projeto}, fase de {fase_atual}
            Público-alvo: Todos os stakeholders
            Pontos-chave:
            - Mudança nos requisitos: {requisitos}
            - Impacto em: {impacto}
            - Ajustes necessários: {ajustes}
            Tom desejado: Formal
            
            O comunicado deve explicar claramente a mudança, justificar sua necessidade, detalhar impactos no projeto
            (cronograma, orçamento, recursos) e apresentar próximos passos para implementação da mudança.
            """
        }
    },
    "Assistente de Reuniões": {
        "Agenda de Reunião de Início de Projeto": {
            "description": "Agenda para kickoff de um novo projeto",
            "template": {
                "context": "Início do projeto {nome_projeto}",
                "participants": "{lista_participantes}",
                "topics": "Apresentações; Visão geral do projeto; Objetivos e escopo; Cronograma preliminar; Papéis e responsabilidades; Próximos passos",
                "duration": 90
            },
            "prompt_template": """
            Crie uma agenda detalhada para uma reunião de kickoff de projeto de 90 minutos com base nas seguintes informações:
            
            Contexto do Projeto: Início do projeto {nome_projeto}
            Participantes: {lista_participantes}
            Tópicos a serem abordados:
            - Apresentações da equipe
            - Visão geral do projeto
            - Objetivos e escopo
            - Cronograma preliminar
            - Papéis e responsabilidades
            - Próximos passos
            
            Inclua alocação de tempo para cada item, responsáveis e objetivos claros para cada segmento da reunião.
            Adicione um espaço para perguntas e discussão ao final.
            """
        },
        "Ata de Reunião de Alinhamento": {
            "description": "Modelo de ata para reuniões de alinhamento de equipe",
            "template": {
                "context": "Projeto {nome_projeto}, fase de {fase_atual}",
                "participants": "{lista_participantes}",
                "topics": "Status atual; Bloqueios; Próximos passos",
                "duration": 30,
                "decisions": "Decisões sobre {decisoes}",
                "actions": "Ações: {acoes}"
            },
            "prompt_template": """
            Crie uma ata/resumo detalhado para uma reunião de alinhamento com base nas seguintes informações:
            
            Contexto do Projeto: Projeto {nome_projeto}, fase de {fase_atual}
            Participantes: {lista_participantes}
            Tópicos abordados:
            - Status atual do projeto
            - Bloqueios identificados
            - Próximos passos
            Decisões tomadas: {decisoes}
            Ações acordadas: {acoes}
            
            Organize por tópicos, destacando claramente decisões e próximos passos com responsáveis e prazos.
            Seja conciso mas completo, focando nas informações mais relevantes.
            """
        }
    },
    "Tradutor de Jargão Técnico": {
        "Explicação de Conceito Técnico para Executivos": {
            "description": "Adaptar explicação técnica para executivos",
            "template": {
                "context": "{contexto}",
                "technical_content": "{conteudo_tecnico}",
                "audience": "Executivos",
                "key_concepts": "{conceitos_chave}"
            },
            "prompt_template": """
            Traduza/adapte o seguinte conteúdo técnico para executivos com base nas seguintes informações:
            
            Contexto do Projeto: {contexto}
            Conteúdo Técnico Original: {conteudo_tecnico}
            Conceitos-chave a preservar: {conceitos_chave}
            
            Para executivos, foque em: 
            - Impacto nos negócios e resultados de alto nível
            - ROI e valor estratégico
            - Riscos e oportunidades principais
            - Decisões necessárias
            
            Use analogias de negócios quando possível e limite a extensão a no máximo dois parágrafos.
            Evite jargão técnico a menos que seja absolutamente necessário.
            """
        }
    },
    "Facilitador de Feedback": {
        "Feedback sobre Entrega Atrasada": {
            "description": "Estrutura de feedback para atrasos em entregas",
            "template": {
                "context": "Projeto {nome_projeto}",
                "situation": "Atraso na entrega do {entregavel} para o projeto {nome_projeto}",
                "strengths": "Qualidade do trabalho entregue; Comunicação proativa",
                "areas_for_improvement": "Estimativas de tempo; Pedido de ajuda antecipado",
                "relationship": "Membro da equipe direto"
            },
            "prompt_template": """
            Estruture um feedback construtivo sobre atraso em entrega com base nas seguintes informações:
            
            Contexto do Projeto: Projeto {nome_projeto}
            Situação específica: Atraso na entrega do {entregavel}
            Pontos fortes a destacar:
            - Qualidade do trabalho entregue
            - Comunicação proativa dos desafios
            Áreas para melhoria:
            - Estimativas de tempo mais realistas
            - Pedir ajuda mais cedo quando enfrentar obstáculos
            Relação com o receptor: Membro da equipe direto
            
            O feedback deve seguir a estrutura SBI (Situação-Comportamento-Impacto) e incluir perguntas
            para entender a perspectiva do colaborador, além de um plano conjunto para melhoria.
            """
        }
    },
    "Detector de Riscos de Comunicação": {
        "Análise de Proposta para Cliente": {
            "description": "Análise de riscos em proposta comercial",
            "template": {
                "context": "Nova proposta para o cliente {nome_cliente}",
                "content_to_analyze": "{conteudo_proposta}",
                "audience": "Cliente potencial, decisores de negócio",
                "stakes": "Alta"
            },
            "prompt_template": """
            Analise a seguinte proposta comercial quanto a riscos de comunicação:
            
            Contexto do Projeto: Nova proposta para o cliente {nome_cliente}
            Público-alvo: Decisores de negócio com conhecimento técnico limitado
            Importância da comunicação: Alta
            
            Conteúdo para análise:
            ---
            {conteudo_proposta}
            ---
            
            Sua análise deve:
            1. Identificar promessas vagas ou arriscadas
            2. Detectar linguagem técnica que pode confundir o público-alvo
            3. Encontrar possíveis ambiguidades em escopo, prazos ou deliverables
            4. Identificar termos que podem gerar expectativas irrealistas
            5. Sugerir reformulações específicas para cada problema identificado
            
            Organize como tabela com: Trecho problemático, Risco potencial, Sugestão de melhoria.
            Ao final, forneça uma avaliação geral dos riscos e recomendações-chave.
            """
        }
    }
}

# ================= SESSION STATE INITIALIZATION =================

# Inicialização da sessão
if 'api_key_configured' not in st.session_state:
    st.session_state.api_key_configured = True
    # Configurar API key automaticamente a partir dos secrets
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
if 'openai_cache' not in st.session_state:
    st.session_state.openai_cache = OpenAICache()
if 'history_expanded' not in st.session_state:
    st.session_state.history_expanded = False
if 'model_choice' not in st.session_state:
    st.session_state.model_choice = "gpt-3.5-turbo"
if 'export_format' not in st.session_state:
    st.session_state.export_format = "text"

# ================= HELPER FUNCTIONS =================

# Função para gerar conteúdo via API OpenAI com cache
def generate_content(prompt, model="gpt-3.5-turbo", temperature=0.7):
    if not st.session_state.api_key_configured or not st.session_state.api_key:
        return "API não configurada. Por favor, contate o administrador."
    
    # Verificar limites
    if st.session_state.token_count >= TOKEN_LIMIT:
        return "Você atingiu o limite de tokens para esta sessão. Por favor, tente novamente mais tarde."
    
    if st.session_state.request_count >= REQUEST_LIMIT:
        return "Você atingiu o limite de requisições para esta sessão. Por favor, tente novamente mais tarde."
    
    # Verificar limites de taxa (rate limits)
    current_time = time.time()
    if current_time - st.session_state.last_request_time < RATE_LIMIT_SECONDS and st.session_state.request_count > 0:
        wait_time = round(RATE_LIMIT_SECONDS - (current_time - st.session_state.last_request_time))
        return f"Por favor, aguarde {wait_time} segundos antes de fazer outra requisição."
    
    # Tentar buscar resposta do cache
    cache_result = st.session_state.openai_cache.get_from_cache(prompt, model, temperature)
    
    if cache_result:
        # Usar cache e atualizar contadores
        content = cache_result['response']['choices'][0]['message']['content']
        
        # Atualizar contadores de tokens (usando valores do cache)
        total_tokens = cache_result['response']['usage']['total_tokens']
        st.session_state.token_count += total_tokens
        
        # Não incrementa o contador de requisições pois usou cache
        # Mas atualiza o timestamp da última requisição para evitar spam
        st.session_state.last_request_time = current_time
        
        # Registrar uso (marcando como cache)
        st.session_state.usage_data.append({
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'feature': st.session_state.current_feature,
            'tokens': total_tokens,
            'model': model,
            'session_id': st.session_state.session_id,
            'from_cache': True
        })
        
        # Adicionar ao histórico
        st.session_state.history.append({
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'feature': st.session_state.current_feature,
            'input': prompt[:100] + "..." if len(prompt) > 100 else prompt,
            'output': content,
            'model': model,
            'session_id': st.session_state.session_id,
            'from_cache': True
        })
        
        return content
    
    try:
        with st.spinner("Gerando conteúdo..."):
            # Atualizar o timestamp da última requisição
            st.session_state.last_request_time = current_time
            
            # Incrementar contador de requisições
            st.session_state.request_count += 1
            
            # Configurar requisição direta à API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {st.session_state.api_key}"
            }
            
            # Adicionar mensagem do sistema e prompt do usuário
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": 1500  # Limitado para economizar tokens
            }
            
            # Fazer a requisição à API
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                data=json.dumps(payload),
                timeout=60
            )
            
            # Processar a resposta
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Atualizar contadores de tokens
                prompt_tokens = result['usage']['prompt_tokens']
                completion_tokens = result['usage']['completion_tokens']
                total_tokens = result['usage']['total_tokens']
                st.session_state.token_count += total_tokens
                
                # Registrar uso
                st.session_state.usage_data.append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'feature': st.session_state.current_feature,
                    'tokens': total_tokens,
                    'model': model,
                    'session_id': st.session_state.session_id,
                    'from_cache': False
                })
                
                # Adicionar ao histórico
                st.session_state.history.append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'feature': st.session_state.current_feature,
                    'input': prompt[:100] + "..." if len(prompt) > 100 else prompt,
                    'output': content,
                    'model': model,
                    'session_id': st.session_state.session_id,
                    'from_cache': False
                })
                
                # Salvar no cache para uso futuro
                st.session_state.openai_cache.save_to_cache(prompt, model, temperature, result)
                
                return content
            else:
                return f"Erro na API (Status {response.status_code}): {response.text}"
        
    except Exception as e:
        return f"Erro ao gerar conteúdo: {str(e)}"

# Função para exportar conteúdo como DOCX
def export_as_docx(content, filename="documento"):
    doc = docx.Document()
    
    # Adicionar título
    doc.add_heading(f"{st.session_state.current_feature}", 0)
    
    # Dividir por linhas e adicionar parágrafos
    paragraphs = content.split('\n')
    for para in paragraphs:
        if para.strip() == "":
            continue
        
        #
