import streamlit as st
from openai import OpenAI
import pandas as pd
from datetime import datetime
import plotly.express as px
import os
import re
import docx
from io import BytesIO

# Configuração da página
st.set_page_config(
    page_title="NEXUS - Assistente de Comunicação de Projetos",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
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
</style>
""", unsafe_allow_html=True)

# Inicialização da sessão
if 'client' not in st.session_state:
    st.session_state.client = None
if 'usage_data' not in st.session_state:
    st.session_state.usage_data = []
if 'api_key_configured' not in st.session_state:
    st.session_state.api_key_configured = False
if 'generated_content' not in st.session_state:
    st.session_state.generated_content = ""
if 'history' not in st.session_state:
    st.session_state.history = []

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
    temperature = st.slider("Temperatura (Criatividade)", 0.0, 1.0, 0.7, 0.1)
    
    # Exibir estatísticas
    if st.session_state.usage_data:
        st.markdown("### Estatísticas de Uso")
        usage_df = pd.DataFrame(st.session_state.usage_data)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Total de Gerações", len(usage_df))
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            if 'tokens' in usage_df.columns:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Tokens Utilizados", usage_df['tokens'].sum())
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Gráfico de uso por categoria
        if 'feature' in usage_df.columns and len(usage_df) > 1:
            feature_counts = usage_df['feature'].value_counts().reset_index()
            feature_counts.columns = ['Funcionalidade', 'Contagem']
            
            fig = px.bar(feature_counts, x='Funcionalidade', y='Contagem', 
                        title='Uso por Funcionalidade',
                        color='Funcionalidade')
            st.plotly_chart(fig, use_container_width=True)
    
    # Feedback
    st.markdown("### Feedback")
    feedback = st.radio("Como está sua experiência?", ["😀 Excelente", "🙂 Boa", "😐 Neutra", "🙁 Ruim", "😞 Péssima"])
    feedback_text = st.text_area("Comentários adicionais")
    
    if st.button("Enviar Feedback"):
        st.success("Feedback enviado. Obrigado por nos ajudar a melhorar!")
    
    st.markdown("</div>", unsafe_allow_html=True)

# Função para gerar conteúdo via OpenAI
def generate_content(prompt, model="gpt-3.5-turbo", temperature=0.7):
    if not st.session_state.client:
        return "Por favor, configure sua API key na barra lateral."
    
    try:
        with st.spinner("Gerando conteúdo..."):
            response = st.session_state.client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system_prompt}, 
                          {"role": "user", "content": prompt}],
                temperature=temperature
            )
        
        result = response.choices[0].message.content
        
        # Registrar uso
        st.session_state.usage_data.append({
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'feature': current_feature,
            'tokens': response.usage.total_tokens,
            'model': model
        })
        
        # Adicionar ao histórico
        st.session_state.history.append({
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'feature': current_feature,
            'input': prompt,
            'output': result,
            'model': model
        })
        
        return result
    
    except Exception as e:
        return f"Erro ao gerar conteúdo: {str(e)}"

# Função para exportar conteúdo como DOCX
def export_as_docx(content, filename="documento"):
    doc = docx.Document()
    
    # Adicionar título
    doc.add_heading(f"{current_feature}", 0)
    
    # Dividir por linhas e adicionar parágrafos
    paragraphs = content.split('\n')
    for para in paragraphs:
        if para.strip() == "":
            continue
        
        # Verificar se é um cabeçalho
        if re.match(r'^#{1,6}\s+', para):
            # Extrair o nível do cabeçalho e o texto
            header_match = re.match(r'^(#{1,6})\s+(.*)', para)
            if header_match:
                level = min(len(header_match.group(1)), 9)  # Limitar a 9 para evitar erro
                text = header_match.group(2)
                doc.add_heading(text, level)
        else:
            doc.add_paragraph(para)
    
    # Salvar para um buffer em memória
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    return buffer

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
"""

# Interface principal
st.markdown('<h1 class="main-header">NEXUS</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Comunicação de projetos clara, eficaz e profissional</p>', unsafe_allow_html=True)

# Seleção de funcionalidade
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

# Inicializar variável para rastrear funcionalidade atual
current_feature = ""

# Organizar opções em colunas
col1, col2 = st.columns(2)

count = 0
for feature, details in feature_options.items():
    if count % 2 == 0:
        with col1:
            with st.expander(f"{details['icon']} {feature}", expanded=False):
                st.markdown(f"**{details['description']}**")
                if st.button(f"Usar {feature}", key=f"select_{feature}"):
                    current_feature = feature
                    st.session_state.current_feature = feature
    else:
        with col2:
            with st.expander(f"{details['icon']} {feature}", expanded=False):
                st.markdown(f"**{details['description']}**")
                if st.button(f"Usar {feature}", key=f"select_{feature}"):
                    current_feature = feature
                    st.session_state.current_feature = feature
    count += 1

# Se uma funcionalidade foi selecionada na sessão atual ou anteriormente
if 'current_feature' in st.session_state and st.session_state.current_feature:
    current_feature = st.session_state.current_feature
    feature_details = feature_options[current_feature]
    
    st.markdown(f"## {feature_details['icon']} {current_feature}")
    
    # Interface específica da funcionalidade
    with st.form(key=f"{current_feature}_form"):
        st.markdown(f"**{feature_details['description']}**")
        
        # Campo de subtipo
        subtype = st.selectbox("Tipo de Comunicação", feature_details['subtypes'])
        
        # Campos comuns a todas as funcionalidades
        context = st.text_area("Contexto do Projeto", 
                              help="Descreva o projeto, fase atual e informações relevantes",
                              height=100)
        
        # Campos específicos por funcionalidade
        if current_feature == "Gerador de Comunicações Estruturadas":
            audience = st.text_input("Público-alvo", 
                                   help="Para quem esta comunicação será enviada (equipe, cliente, stakeholder)")
            key_points = st.text_area("Pontos-chave", 
                                    help="Liste os principais pontos que devem ser incluídos na comunicação",
                                    height=150)
            tone = st.select_slider("Tom da Comunicação", 
                                  options=["Muito Formal", "Formal", "Neutro", "Amigável", "Casual"],
                                  value="Neutro")
            
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
                                      height=100)
            topics = st.text_area("Tópicos a serem abordados", 
                                help="Liste os tópicos que precisam ser discutidos",
                                height=150)
            duration = st.number_input("Duração (minutos)", min_value=15, max_value=240, value=60, step=15)
            
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
                                       height=100)
                actions = st.text_area("Ações acordadas", 
                                     help="Liste as ações acordadas, responsáveis e prazos",
                                     height=100)
                
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
                                             height=100)
                action_items = st.text_area("Itens de ação", 
                                          help="Liste os itens de ação, responsáveis e prazos",
                                          height=100)
                
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
                                           height=200)
            audience = st.selectbox("Público-alvo", 
                                  ["Executivos", "Clientes não-técnicos", "Equipe de Negócios", "Equipe Técnica Junior"])
            key_concepts = st.text_input("Conceitos-chave a preservar", 
                                       help="Liste conceitos técnicos que devem ser mantidos mesmo se simplificados")
            
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
                                   height=150)
            strengths = st.text_area("Pontos Fortes", 
                                   help="Liste aspectos positivos que devem ser destacados",
                                   height=100)
            areas_for_improvement = st.text_area("Áreas para Melhoria", 
                                               help="Liste aspectos que precisam ser melhorados",
                                               height=100)
            relationship = st.selectbox("Relação com o Receptor", 
                                      ["Membro da equipe direto", "Colega de mesmo nível", "Superior hierárquico", "Cliente", "Fornecedor"])
            
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
                                            height=200)
            audience = st.text_input("Público-alvo", 
                                   help="Descreva quem receberá esta comunicação")
            stakes = st.select_slider("Importância da Comunicação", 
                                    options=["Baixa", "Média", "Alta", "Crítica"],
                                    value="Média")
            
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
        
        submit_button = st.form_submit_button(f"Gerar {current_feature}")
    
    if submit_button:
        if st.session_state.api_key_configured:
            # Gerar conteúdo
            generated_content = generate_content(prompt, model, temperature)
            st.session_state.generated_content = generated_content
            
            # Exibir resultado
            st.markdown("### Resultado")
            st.markdown('<div class="result-area">', unsafe_allow_html=True)
            st.markdown(generated_content)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Opções de download
            col1, col2 = st.columns(2)
            with col1:
                # Download como texto
                st.download_button(
                    label="📄 Baixar como TXT",
                    data=generated_content,
                    file_name=f"{current_feature.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
            
            with col2:
                # Download como DOCX
                docx_buffer = export_as_docx(generated_content)
                st.download_button(
                    label="📝 Baixar como DOCX",
                    data=docx_buffer,
                    file_name=f"{current_feature.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            
            # Feedback sobre o resultado
            st.markdown("### Este resultado foi útil?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("👍 Sim, foi útil"):
                    st.markdown('<p class="feedback-good">Obrigado pelo feedback positivo!</p>', unsafe_allow_html=True)
            
            with col2:
                if st.button("👎 Não, preciso de melhoria"):
                    st.markdown('<p class="feedback-bad">Lamentamos que não tenha atendido suas expectativas. Por favor, forneça detalhes no campo de feedback na barra lateral para podermos melhorar.</p>', unsafe_allow_html=True)
        else:
            st.warning("Por favor, configure sua API key da OpenAI na barra lateral para continuar.")

# Histórico de gerações recentes
if st.session_state.history:
    with st.expander("Histórico de Gerações Recentes", expanded=False):
        for i, item in enumerate(reversed(st.session_state.history[-5:])):
            st.markdown(f"**{item['timestamp']} - {item['feature']}**")
            if st.button(f"Carregar este conteúdo ↩️", key=f"load_{i}"):
                st.session_state.current_feature = item['feature']
                st.session_state.generated_content = item['output']
                st.experimental_rerun()
            st.markdown("---")

# Rodapé com créditos
st.markdown("""
---
<div style="text-align: center; color: gray; font-size: 0.8rem;">
    NEXUS | Assistente de Comunicação de Projetos | Criado para gerenciar comunicações de projetos com eficiência
</div>
""", unsafe_allow_html=True)
