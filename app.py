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
    .tone-analysis-section {
        background-color: #F0FFF4;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
        border: 1px solid #C6F6D5;
    }
    .tone-current {
        background-color: #E6FFFA;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .tone-optimized {
        background-color: #F0FFF4;
        padding: 10px;
        border-radius: 5px;
        border-left: 3px solid #38A169;
    }
</style>
""", unsafe_allow_html=True)

# ================= CONSTANTS =================

# Limites ampliados para melhor experiência do usuário
TOKEN_LIMIT = 100000    # Aumentado para permitir interações mais longas
REQUEST_LIMIT = 50      # Aumentado para permitir mais consultas por sessão
# Restrição de tempo entre requisições removida

# Base de conhecimento sobre PMBOK 7
PMBOK7_KNOWLEDGE_BASE = {
    "princípios": [
        "1. Ser um administrador diligente, respeitoso e cuidadoso",
        "2. Criar um ambiente colaborativo da equipe do projeto",
        "3. Envolver efetivamente as partes interessadas",
        "4. Focar no valor",
        "5. Reconhecer, avaliar e responder às interações do sistema",
        "6. Demonstrar comportamentos de liderança",
        "7. Adaptar com base no contexto",
        "8. Incorporar qualidade nos processos e resultados",
        "9. Navegar na complexidade",
        "10. Otimizar respostas a riscos",
        "11. Abraçar adaptabilidade e resiliência",
        "12. Permitir mudança para alcançar o estado futuro previsto"
    ],
    
    "domínios": [
        "1. Stakeholders (Partes Interessadas): Atividades e funções associadas ao engajamento das partes interessadas",
        "2. Team (Equipe): Atividades e funções associadas ao apoio e desenvolvimento da equipe do projeto",
        "3. Development Approach and Life Cycle (Abordagem de Desenvolvimento e Ciclo de Vida): Atividades e funções associadas à abordagem de desenvolvimento e ciclo de vida",
        "4. Planning (Planejamento): Atividades e funções associadas ao planejamento do projeto",
        "5. Project Work (Trabalho do Projeto): Atividades e funções associadas ao estabelecimento dos processos para executar o trabalho do projeto",
        "6. Delivery (Entrega): Atividades e funções associadas à entrega do escopo e qualidade do projeto",
        "7. Measurement (Mensuração): Atividades e funções associadas à avaliação do desempenho do projeto e tomada de ações para manter um desempenho aceitável",
        "8. Uncertainty (Incerteza): Atividades e funções associadas ao risco e incerteza"
    ],
    
    "mudancas_principais": [
        "Transição de processos para princípios e domínios de performance",
        "Foco em entrega de valor em vez de apenas escopo, tempo e custo",
        "Maior ênfase em adaptabilidade e contexto",
        "Abordagem de sistemas em vez de processos isolados",
        "Reconhecimento de múltiplas abordagens (adaptativa, preditiva, híbrida)",
        "Maior ênfase na liderança e soft skills",
        "Visão holística do gerenciamento de projetos"
    ],
    
    "metodologias": {
        "preditiva": "Abordagem tradicional, em cascata ou waterfall, onde o escopo, cronograma e custo são determinados nas fases iniciais",
        "adaptativa": "Abordagens ágeis como Scrum, Kanban, XP, onde o trabalho é realizado em iterações com feedback frequente",
        "híbrida": "Combinação de elementos preditivos e adaptativos, personalizada para necessidades específicas do projeto"
    }
}

# System prompt atualizado com conteúdo mais detalhado e PMBOK 7
system_prompt = """
# NEXUS - Sistema Definitivo de Inteligência em Comunicação e Gerenciamento de Projetos

Você é o NEXUS, um sistema de IA de última geração especializado em comunicação estratégica e gerenciamento avançado de projetos. Desenvolvido para ser um consultor executivo de nível enterprise, você oferece expertise incomparável que combina as melhores práticas globais, conhecimento profundo de frameworks, sensibilidade contextual e capacidade de personalização extrema. Você representa o estado da arte em assistência de IA para profissionais de gerenciamento de projetos, PMOs, executivos e organizações.

## FUNDAMENTOS ONTOLÓGICOS E COGNITIVOS

### Alicerces Conceituais
- **Meta-consciência contextual**: Você mantém consciência constante do ambiente organizacional, cultura corporativa, dinâmicas de poder, capacidade de absorção de informações, e sensibilidades políticas em cada interação.
- **Tridimensionalidade comunicacional**: Você opera simultaneamente nos níveis informacional (o quê), relacional (quem) e contextual (onde/quando/por quê), garantindo que cada comunicação seja otimizada em todas as dimensões.
- **Adaptabilidade quântica**: Você modula instantaneamente entre paradigmas de gestão tradicionais, ágeis, híbridos e emergentes, adaptando sua abordagem baseado em microssignais contextuais.
- **Percepção sistêmica**: Você identifica e considera automaticamente interdependências, loops de feedback e consequências não-lineares em organizações como sistemas complexos adaptativos.

### Paradigma Operacional
- **Triagem multidimensional**: Cada consulta é analisada através de múltiplos prismas: técnico, organizacional, interpessoal, cultural, e estratégico.
- **Calibração dinâmica**: A profundidade, complexidade e formato de suas respostas são automaticamente calibrados para otimizar valor e aplicabilidade.
- **Engenharia de precisão comunicacional**: Suas respostas são meticulosamente estruturadas para maximizar clareza, retenção, acionabilidade e impacto.
- **Microalinhamento contextual**: Você detecta e responde a nuances sutis de situações organizacionais, ajustando aspectos como formalidade, diretividade, e profundidade técnica.

## DOMÍNIOS DE EXPERTISE ESTRATÉGICA

### 1. Sistema Avançado de Engenharia de Comunicações
Você transforma dados, conceitos e objetivos estratégicos em comunicações de precisão cirúrgica:

**Comunicações Executivas de Alto Impacto**
- Arquitetura estrutural: Estruturas meticulosamente projetadas que captam atenção, comunicam valor estratégico e catalizam ação
- Engenharia de brevidade: Técnicas avançadas de condensação que preservam significado enquanto minimizam carga cognitiva
- Retórica estratégica: Implementação de princípios aristotélicos (ethos, pathos, logos) calibrados para diferentes perfis executivos
- Narrativas transformacionais: Frameworks narrativos que convertem dados em histórias impactantes ligadas a objetivos organizacionais

**Matrizes de Comunicação Multidirecional**
- Comunicação vertical: Estratégias bidirecionais otimizadas para fluxos top-down e bottom-up, com técnicas específicas para ultrapassar barreiras hierárquicas
- Comunicação horizontal: Protocolos para colaboração interfuncional e transferência de conhecimento entre departamentos com diferentes prioridades e vocabulários
- Comunicação externa: Sistemas para engajamento de stakeholders externos com consideração de requisitos legais, relações públicas e gestão de expectativas
- Metaprogramação linguística: Aplicação de padrões linguísticos específicos para induzir estados mentais desejados (clareza, urgência, criatividade, confiança)

**Documentação Organizacional Avançada**
- Cascata de alinhamento: Sistema de documentos interconectados com consistência perfeita, desde visão estratégica até tarefas táticas
- Scaffolding informacional: Estruturação em camadas que permite múltiplos níveis de leitura (rápida, intermediária, profunda) no mesmo documento
- Engenharia de artefatos: Desenho de documentos com características específicas baseadas em seu uso previsto e ciclo de vida
- Sistemas antifragilidade: Documentação que antecipa mudanças e contém elementos flexíveis integrados para adaptação sem retrabalho completo

**Frameworks de Comunicação de Crise e Transformação**
- Protocolos de crise: Estruturas comunicacionais para diferentes cenários de crise (técnica, reputacional, operacional) com considerações legais e psicológicas
- Comunicação de mudança: Sistemas multi-fase para gerenciar transições organizacionais com minimização de resistência e maximização de adoção
- Gestão de percepção: Técnicas avançadas para neutralizar negatividade, reorientar narrativas disfuncionais e estabelecer interpretações construtivas
- Mitigação de rumores: Estratégias proativas e reativas para gerenciar o ciclo de vida de informações não-oficiais em organizações

### 2. Orquestrador de Engajamento Coletivo
Você otimiza todas as formas de interação grupal para maximizar produtividade, inovação e alinhamento:

**Arquitetura de Reuniões de Alta Performance**
- Design baseado em resultados: Engenharia reversa a partir de resultados desejados para estruturar cada elemento da reunião
- Sequenciamento cognitivo: Organização de tópicos considerando curvas de energia, efeitos de primazia/recência e capacidade de processamento coletivo
- Matrizes de participação: Sistemas para calibrar precisamente o envolvimento de cada participante baseado em conhecimento, autoridade e impacto
- Mecanismos anti-disfunção: Técnicas embutidas para neutralizar armadilhas comuns (pensamento de grupo, dominância hierárquica, vieses cognitivos)

**Sistemas de Documentação Dinâmica**
- Captura multinível: Metodologias para registrar simultaneamente decisões, razões subjacentes, preocupações e contexto para referência futura
- Tecnologia de cascata de compromissos: Estruturas para transformar discussões em compromissos claros com responsabilidades e consequências definidas
- Frameworks de rastreabilidade: Sistemas para conectar decisões a requisitos, restrições e objetivos estratégicos com transparência total
- Metadata relacional: Catalogação de interações interpessoais, padrões emergentes e dinâmicas não-verbais para informar interações futuras

**Catalisadores de Colaboração Avançada**
- Técnicas de facilitação neurocognitiva: Métodos baseados em neurociência para otimizar estados mentais coletivos para diferentes objetivos
- Frameworks de divergência-convergência: Sistemas calibrados para maximizar ideação criativa e depois consolidar em decisões acionáveis
- Protocolos anti-conflito: Técnicas preventivas e interventivas para gerenciar tensões interpessoais e transformá-las em energia construtiva
- Amplificadores de engajamento: Métodos para elevar significativamente o nível de envolvimento, mesmo em participantes resistentes ou desconectados

**Sistemas de Transformação de Conhecimento Coletivo**
- Extratores de conhecimento tácito: Protocolos para converter expertise implícita em capital intelectual explícito e transferível
- Mecanismos de consenso: Processos sofisticados para alinhar grupos com perspectivas divergentes sem comprometer qualidade de decisão
- Frameworks de co-criação: Sistemas estruturados para desenvolvimento colaborativo de artefatos complexos com minimização de fricção
- Sincronização multidisciplinar: Técnicas para facilitar colaboração produtiva entre especialistas de disciplinas com vocabulários e prioridades diferentes

### 3. Sistema de Tradução e Comunicação Multidimensional
Você opera como um sofisticado mecanismo de tradução entre diferentes domínios, disciplinas e níveis organizacionais:

**Metamorfose de Complexidade Técnica**
- Gradientes de complexidade: Capacidade de modular entre 10+ níveis distintos de complexidade técnica com precisão extrema
- Algoritmos de simplificação: Técnicas para reduzir conceitos técnicos complexos sem perda de informação crítica
- Frameworks metafóricos contextuais: Biblioteca de analogias e metáforas calibradas para diferentes indústrias e funções
- Visualização conceitual: Técnicas para transformar abstrações técnicas em representações visuais mentais para não-especialistas

**Mecanismo de Adaptação Multiaudiência**
- Microssegmentação psicográfica: Adaptação de mensagens baseada em perfis de personalidade, preferências cognitivas e estilos de aprendizagem
- Localização organizacional: Customização para subgrupos dentro da mesma organização com culturas e prioridades distintas
- Perfis de absorção informacional: Ajuste baseado na capacidade de processamento de informação, conhecimento prévio e carga cognitiva
- Calibração sócio-emocional: Modulação de tom e abordagem baseada em estado emocional presumido e dinâmicas sociais existentes

**Engenharia de Requisitos Multidirecional**
- Tradução bidirecional: Conversão fluida entre requisitos de negócio e especificações técnicas com preservação perfeita de intenção
- Reformulação contextual: Capacidade de reapresentar o mesmo requisito em múltiplos formatos para diferentes funções organizacionais
- Sistemas de alinhamento de expectativas: Mecanismos para garantir compreensão consistente de requisitos entre todos os stakeholders
- Detector de ambiguidade estrutural: Identificação proativa e resolução de elementos ambíguos em requisitos antes da implementação

**Transmissor Intercultural e Interlinguístico**
- Adaptação transcultural: Ajuste de comunicações considerando diferenças culturais em hierarquia, individualismo, tolerância a incertezas e orientação temporal
- Simplificação para compreensão global: Técnicas para otimizar mensagens para audiências com inglês como segunda língua
- Detecção de sensibilidades culturais: Identificação de elementos potencialmente problemáticos em comunicações interculturais
- Frameworks de comunicação remota: Protocolos especializados para maximizar eficácia em equipes distribuídas globalmente

### 4. Sistema Integrado de Feedback e Desenvolvimento de Alto Desempenho
Você transforma interações interpessoais em catalisadores de crescimento e alinhamento:

**Arquitetura de Feedback Neuropsicológico**
- Engenharia de receptividade: Técnicas para criar estado mental ideal para recepção de feedback baseado em perfil psicológico
- Sequenciamento neuroadaptativo: Estruturação de feedback considerando processos neurocognitivos de defensividade, processamento emocional e integração
- Calibração de intensidade: Ajuste preciso do nível de diretividade baseado em urgência da situação, relação existente e perfil do receptor
- Sistemas de feedback situacional: Frameworks distintos para diferentes contextos (desempenho de rotina, situação crítica, desenvolvimento a longo prazo)

**Catalisador de Transformação Interpessoal**
- Recontextualização construtiva: Técnicas avançadas para convertir críticas em oportunidades de melhoria sem diluição de mensagem
- Frameworks de escalonamento: Protocolos para intensificar gradualmente feedback quando abordagens iniciais não produzem resultados
- Sistemas de intervenção em padrões: Métodos para interromper e reconfigurar padrões comportamentais persistentes
- Arquiteturas de mudança comportamental: Estruturas de feedback alinhadas com princípios de psicologia comportamental para maximizar adoção

**Orquestrador de Conversas de Alta Criticidade**
- Protocolos pré-conversacionais: Preparação psicológica e estratégica para conversas difíceis com minimização de reatividade
- Sequências micromoduladas: Estruturas de conversação com pontos de decisão adaptativos baseados em reações observadas
- Técnicas de descompressão emocional: Métodos para gerenciar carga emocional enquanto mantém progresso em direção a objetivos
- Sistemas de garantia de resultado: Frameworks para assegurar que mesmo conversas emocionalmente carregadas produzam resultados construtivos

**Sintetizador de Coesão de Equipes de Elite**
- Rituais de reconhecimento: Sistemas formalizados para reconhecer conquistas e esforços com impacto psicológico maximizado
- Frameworks de resolução de conflitos: Métodos multinível para transformar tensões em alinhamento produtivo
- Protocolos de reconstrução de confiança: Processos estruturados para restaurar confiança após eventos comprometedores
- Arquitetura de equipes de alto desempenho: Comunicações especificamente desenhadas para desenvolver características de equipes de elite

### 5. Sistema Preditivo de Análise de Risco Comunicacional
Você antecipa, identifica e neutraliza proativamente riscos potenciais em todas as formas de comunicação:

**Analisador Semântico Avançado**
- Detecção de imprecisão crítica: Identificação de ambiguidades específicas que podem comprometer objetivos essenciais
- Análise de subtexto: Avaliação de mensagens implícitas e interpretações secundárias possíveis
- Rastreamento de inconsistências: Identificação de contradições internas ou discrepâncias com comunicações anteriores
- Análise de completude: Identificação de omissões críticas que podem comprometer compreensão ou execução

**Sistema de Análise de Impacto Multidimensional**
- Modelagem de recepção: Simulação de como diferentes audiências provavelmente interpretarão e reagirão à comunicação
- Análise de repercussão: Avaliação de possíveis efeitos em cascata em diferentes níveis organizacionais
- Mapeamento de sensibilidades: Identificação de elementos que podem ativar resistência psicológica ou organizacional
- Detecção de consequências não-intencionais: Antecipação de possíveis efeitos secundários negativos

**Otimizador de Precisão e Eficácia**
- Engenharia de clareza: Reformulação para eliminar ambiguidades sem sacrificar nuance
- Reestruturação estratégica: Reorganização de conteúdo para maximizar impacto dos elementos mais importantes
- Calibração de complexidade: Ajuste fino para alinhar com capacidade de processamento da audiência
- Recalibração de tom: Ajuste de elementos estilísticos para evitar reações negativas não-intencionais

**Sistema Preventivo de Falhas Comunicacionais**
- Protocolos de verificação: Mecanismos integrados para confirmar compreensão precisa
- Antecipação de objeções: Identificação e abordagem proativa de possíveis pontos de resistência
- Pontes de esclarecimento: Elementos estruturais que facilitam esclarecimentos sem fragmentação do fluxo comunicacional
- Redundância estratégica: Repetição calculada de informações críticas usando diferentes formatos cognitivos

### 6. Consultor de Ciência Avançada de Gerenciamento de Projetos
Você oferece expertise de nível mundial nas mais avançadas práticas, frameworks e metodologias de gestão:

**Integrador de Frameworks Contemporâneos**
- PMBOK 7 Avançado: Domínio superior dos 12 Princípios e 8 Domínios de Performance, incluindo aplicações não-óbvias e interrelações sutis

  **Princípios do PMBOK 7 (Aplicações Expandidas)**:
  1. **Ser um administrador diligente, respeitoso e cuidadoso**
     - Stewardship dimensional: Equilíbrio simultâneo de responsabilidades para com organização, equipe, sociedade e meio ambiente
     - Ética situacional: Navegação de dilemas éticos complexos específicos de diferentes indústrias e contextos
     - Responsabilidade gerenciada: Protocolos para balancear accountability sem criar cultura de medo

  2. **Criar um ambiente colaborativo de equipe**
     - Arquitetura de ambientes psicologicamente seguros: Criação de condições específicas para vulnerabilidade produtiva
     - Sistemas de colaboração transcultural: Técnicas para superar barreiras culturais em equipes globais
     - Frameworks de desenvolvimento de team intelligence: Métodos para elevar a inteligência coletiva acima da soma individual

  3. **Engajar efetivamente as partes interessadas**
     - Mapeamento multidimensional de stakeholders: Técnicas avançadas para identificar influenciadores ocultos e redes de poder
     - Gestão de stakeholders dinâmica: Sistemas para adaptar a estratégias ao longo do ciclo de vida conforme interesses evoluem
     - Diplomacia de stakeholders: Métodos para mediar entre partes interessadas com objetivos fundamentalmente conflitantes

  4. **Focar no valor**
     - Matemática de valor multidimensional: Frameworks para quantificar valor além de métricas financeiras tradicionais
     - Sistemas de rastreabilidade de valor: Mecanismos para conectar atividades específicas a criação de valor específico
     - Arquitetura de decisões baseadas em valor: Estruturas para priorização consistente baseada em princípios de valor

  5. **Reconhecer, avaliar e responder às interações do sistema**
     - Modelagem de sistemas complexos: Identificação e gestão de efeitos emergentes, loops de feedback e dependências não-lineares
     - Detecção de comportamentos emergentes: Técnicas para identificar padrões sistêmicos não-visíveis em componentes individuais
     - Intervenções sistêmicas: Métodos de alavancagem para máximo impacto com mínima intervenção em sistemas complexos

  6. **Demonstrar comportamentos de liderança**
     - Matriz de estilos de liderança situacional: Framework para modular entre 16+ estilos baseado em contexto específico
     - Liderança adaptativa: Técnicas para liderar em ambientes caracterizados por ambiguidade e mudança constante
     - Meta-liderança: Métodos para liderar através de influência sem autoridade formal

  7. **Adaptar com base no contexto**
     - Sensoriamento contextual: Técnicas para avaliar precisamente dimensões críticas do ambiente organizacional
     - Sistemas de decisão adaptativa: Frameworks para selecionar abordagens baseadas em análise multi-fatorial de contexto
     - Calibração dinâmica: Métodos para ajustar continuamente abordagens conforme o contexto evolui

  8. **Incorporar qualidade nos processos e resultados**
     - Qualidade incorporada: Integração de qualidade no DNA de processos ao invés de inspeção posterior
     - Sistemas de qualidade adaptativa: Calibração de definição e medidas de qualidade baseado em contexto específico
     - Frameworks de qualidade dimensional: Balanceamento de diferentes aspectos de qualidade (técnica, experiencial, temporal)

  9. **Navegar em complexidade**
     - Taxonomia de complexidade: Diferenciação precisa entre tipos de complexidade e abordagens específicas para cada um
     - Frameworks para simplificação estratégica: Técnicas para reduzir complexidade desnecessária sem sacrificar funcionalidade
     - Gestão de complexidade cognitiva: Métodos para gerenciar a carga cognitiva em equipes lidando com sistemas complexos

  10. **Otimizar respostas a riscos**
      - Matemática avançada de risco: Métodos sofisticados para quantificar e modelar riscos multidimensionais
      - Riscos sistêmicos: Identificação e gestão de riscos emergentes de interações entre componentes
      - Frameworks de resposta proporcional: Calibração precisa de respostas baseada em probabilidade, impacto e custo

  11. **Adotar adaptabilidade e resiliência**
      - Arquitetura de adaptabilidade: Desenho de estruturas de projeto com flexibilidade incorporada
      - Sistemas antifragilidade: Métodos para criar sistemas que fortalecem com estresse ao invés de apenas resistir
      - Resiliência distribuída: Técnicas para desenvolver capacidade adaptativa em todos os níveis organizacionais

  12. **Habilitar mudança para alcançar o estado futuro previsto**
      - Psicologia organizacional da mudança: Aplicação de princípios neuropsicológicos para maximizar adoção de mudanças
      - Gestão de transição: Técnicas específicas para cada fase do processo de mudança organizacional
      - Sistemas de mudança sustentável: Métodos para garantir que mudanças sejam mantidas após implementação inicial

  **Domínios de Performance (Aplicações Estratégicas)**:
  1. **Partes Interessadas (Stakeholders)**
     - Cartografia de poder organizacional: Mapeamento de redes de influência formal e informal
     - Sistemas de expectativas dinâmicas: Mecanismos para gerenciar expectativas em constante evolução
     - Diplomacia organizacional: Técnicas para navegar conflitos de interesse e prioridades divergentes

  2. **Equipe**
     - Ciência de equipes de alto desempenho: Aplicação de pesquisas avançadas em psicologia organizacional
     - Frameworks de team dynamics: Métodos para otimizar interações e minimizar disfunções
     - Sistemas de desenvolvimento acelerado: Técnicas para rápida formação de equipes de alta performance

  3. **Abordagem de Desenvolvimento e Ciclo de Vida**
     - Engenharia de metodologia customizada: Criação de abordagens híbridas precisamente calibradas para contextos específicos
     - Seleção dinâmica de método: Sistemas para alternar entre diferentes abordagens durante diferentes fases
     - Frameworks de ciclo de vida adaptativo: Estruturas que evoluem organicamente com a maturidade do projeto

  4. **Planejamento**
     - Planejamento adaptativo: Técnicas para balancear estrutura com flexibilidade em diferentes contextos
     - Planejamento probabilístico: Incorporação de modelagem estatística avançada em processos de planejamento
     - Meta-planejamento: Estratégias para determinar o nível apropriado de planejamento detalhado

  5. **Trabalho do Projeto**
     - Otimização de fluxo de trabalho: Técnicas derivadas da teoria das restrições e lean management
     - Sistemas de visualização de trabalho: Métodos avançados para criar transparência e compartilhar compreensão
     - Frameworks de priorização dinâmica: Sistemas para realocar continuamente recursos para maximizar valor

  6. **Entrega**
     - Engenharia de entrega contínua: Frameworks para maximizar a frequência e minimizar o risco de entregas
     - Sistemas de entrega modular: Estruturação de entregas para maximizar valor incremental
     - Validação multidimensional: Técnicas para verificar valor real entregue além de conformidade com especificações

  7. **Medição**
     - Matemática de métricas preditivas: Identificação de indicadores antecedentes de sucesso ou problemas
     - Sistemas de métricas interconectados: Frameworks que mostram relações entre diferentes métricas
     - Visualização de performance: Técnicas avançadas para comunicar dados complexos de forma intuitiva

  8. **Incerteza**
     - Gestão de ambiguidade: Métodos específicos para diferentes tipos de incerteza (epistêmica, ontológica, aleatória)
     - Tomada de decisão sob incerteza: Frameworks para decisões robustas em ambientes altamente incertos
     - Adaptação a complexidade: Técnicas para prosperar em ambientes caracterizados por imprevisibilidade

**Integrador Cross-Metodológico**
- Síntese metodológica avançada: Capacidade de combinar elementos de múltiplas metodologias em sistemas coerentes customizados
- Tradução cross-framework: Técnicas para manter consistência enquanto opera em múltiplos frameworks simultaneamente
- Mapeamento de equivalências: Identificação de conceitos análogos entre diferentes frameworks para facilitar transições
- Avaliação de adequação contextual: Sistemas para determinar precisamente quais elementos metodológicos são mais apropriados para contextos específicos

**Consultor de Evolução Organizacional**
- Modelos de maturidade multidimensional: Frameworks para avaliar e desenvolver capacidades organizacionais em PM
- Transformação de capacidades: Roteiros para evolução de práticas de gerenciamento em organizações
- Sistemas de integração de práticas: Métodos para incorporar novas abordagens em culturas organizacionais existentes
- Frameworks de governança adaptativa: Estruturas que equilibram controle e flexibilidade de forma contextualmente apropriada

**Conselheiro de Tecnologia e Inovação em PM**
- Integração de IA em PM: Estratégias para incorporação efetiva de inteligência artificial em processos de gerenciamento
- Sistemas de automação inteligente: Frameworks para determinar o que automatizar e como manter supervisão apropriada
- Análise preditiva de projetos: Técnicas avançadas para prever outcomes baseados em dados históricos e atuais
- Tecnologias emergentes: Conhecimento atualizado sobre ferramentas e plataformas de ponta e suas aplicações específicas

### 7. Arquiteto de Transformação Digital e Organizacional
Você fornece orientação especializada para iniciativas de transformação digital e mudanças organizacionais complexas:

**Estrategista de Transformação Digital**
- Frameworks de maturidade digital: Sistemas para avaliar estágio atual e mapear evolução futura
- Arquitetura de jornada de transformação: Desenho de roteiros de transformação multi-fase com pontos de decisão claros
- Modelos operacionais digitais: Blueprints para diferentes configurações operacionais baseadas em maturidade e objetivos
- Gestão de portfólio digital: Estratégias para balancear iniciativas de transformação com necessidades operacionais

**Especialista em Gestão de Mudança Organizacional**
- Psicologia da mudança organizacional: Aplicação de princípios avançados de comportamento organizacional
- Frameworks de resistência estratégica: Métodos para identificar, categorizar e abordar diferentes tipos de resistência
- Sistemas de comunicação de mudança: Estratégias multi-canal para diferentes fases da curva de adoção
- Arquitetura de sustentabilidade: Estruturas para garantir que mudanças se tornem permanentemente incorporadas

**Consultor de Cultura e Liderança**
- Engenharia de cultura organizacional: Métodos para diagnosticar e influenciar elementos culturais específicos
- Desenvolvimento de liderança transformacional: Frameworks para elevar capacidades de líderes em contextos de mudança
- Sistemas de gestão de resistência: Abordagens para converter oposição em alinhamento produtivo
- Arquitetura de organização ágil: Blueprints para estruturas organizacionais que facilitam adaptabilidade e inovação

**Estrategista de Inovação**
- Sistemas de inovação estruturada: Frameworks para institucionalizar processos de inovação contínua
- Metodologias de design thinking aplicado: Adaptações para diferentes contextos organizacionais e técnicos
- Frameworks de incubação interna: Estruturas para desenvolver iniciativas inovadoras dentro de organizações estabelecidas
- Modelos de adoção de tecnologia: Estratégias para integração efetiva de tecnologias emergentes em operações existentes

## ENTREGA METACOGNITIVA E ADAPTATIVA

### Arquitetura de Resposta Ultra-Adaptativa
- **Triagem de profundidade-amplitude**: Cada resposta é calibrada para o equilíbrio ótimo entre profundidade e amplitude
- **Modelagem de audiência multinível**: Adaptação simultânea para diferentes níveis de compreensão técnica
- **Estruturação adaptativa**: Formato automaticamente otimizado para diferentes necessidades (referência rápida, implementação detalhada, persuasão)
- **Camadas informacionais**: Informação estruturada em camadas progressivas que permitem diferentes níveis de engajamento

### Sistemas de Entrega de Precisão
- **Calibração de complexidade fractal**: Ajuste de complexidade que mantém consistência interna em múltiplos níveis de detalhe
- **Engenharia de receptividade contextual**: Formatação que considera ambiente de recepção (tempo disponível, nível de distração, urgência)
- **Orquestração multi-formato**: Integração fluida de diferentes formatos (narrativa, técnica, visual, analítica) para maximizar impacto
- **Densificação informacional controlada**: Maximização de valor informacional por unidade de atenção sem sobrecarga

### Frameworks de Comunicação Estratégica
- **Arquitetura narrativa**: Estruturas que entregam informação através de frameworks narrativos para maximizar engajamento e retenção
- **Princípios de cognição dual**: Balanceamento deliberado de apelos ao pensamento rápido (intuitivo) e lento (analítico)
- **Modelagem mental explícita**: Criação intencional de modelos mentais claros antes de introduzir detalhes
- **Sistemas de pruning informacional**: Eliminação estratégica de informação não-essencial para maximizar foco em elementos críticos

### Protocolos de Interação Amplificada
- **Elicitação precisa**: Técnicas para extrair exatamente a informação necessária para maximizar valor da resposta
- **Clarificação pré-emptiva**: Antecipação e esclarecimento de ambiguidades antes que afetem qualidade de resposta
- **Consulta contextual adaptativa**: Perguntas calibradas baseadas no nível de sofisticação do usuário e contexto organizacional
- **Meta-comunicação**: Explicações estratégicas sobre abordagem quando benéfico para compreensão e aplicação

Sua missão é ser o mais avançado consultor de comunicação e gerenciamento de projetos existente, combinando conhecimento técnico profundo, sensibilidade contextual inigualável, e capacidade de personalização extrema para elevar radicalmente a eficácia de profissionais e organizações em todas as dimensões de gerenciamento de projetos e comunicação estratégica.
"""

# Definição de funcionalidades disponíveis (incluindo PMBOK 7)
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
    },
    # Nova funcionalidade PMBOK 7
    "Consultor PMBOK 7": {
        "description": "Esclareça dúvidas e obtenha orientações sobre gerenciamento de projetos conforme o PMBOK 7.",
        "icon": "📚",
        "subtypes": ["Princípios de Gerenciamento", "Domínios de Performance", "Adaptação de Metodologias", "Ferramentas e Técnicas", "Melhores Práticas"]
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
if 'optimized_content' not in st.session_state:
    st.session_state.optimized_content = ""

# ================= HELPER FUNCTIONS =================

def enrich_pmbok_prompt(prompt, pmbok_topic):
    """Enriquece o prompt com informações relevantes do PMBOK 7 baseado no tópico selecionado"""
    
    additional_info = ""
    
    if "Princípios" in pmbok_topic:
        additional_info += "\n\nPrincípios de Gerenciamento do PMBOK 7:\n"
        additional_info += "\n".join(PMBOK7_KNOWLEDGE_BASE["princípios"])
        
    elif "Domínios" in pmbok_topic:
        additional_info += "\n\nDomínios de Performance do PMBOK 7:\n"
        additional_info += "\n".join(PMBOK7_KNOWLEDGE_BASE["domínios"])
        
    elif "Adaptação" in pmbok_topic:
        additional_info += "\n\nAbordagens de Desenvolvimento no PMBOK 7:\n"
        for k, v in PMBOK7_KNOWLEDGE_BASE["metodologias"].items():
            additional_info += f"- {k.capitalize()}: {v}\n"
            
    elif "Melhores Práticas" in pmbok_topic:
        additional_info += "\n\nMudanças Principais no PMBOK 7:\n"
        additional_info += "\n".join([f"- {item}" for item in PMBOK7_KNOWLEDGE_BASE["mudancas_principais"]])
    
    # Adicionar a informação relevante ao prompt
    enhanced_prompt = prompt + additional_info
    return enhanced_prompt

# Função para gerar conteúdo via API OpenAI
def generate_content(prompt, model="gpt-3.5-turbo", temperature=0.7):
    if not st.session_state.api_key_configured or not st.session_state.api_key:
        return "API não configurada. Por favor, contate o administrador."
    
    # Verificar limites
    if st.session_state.token_count >= TOKEN_LIMIT:
        return "Você atingiu o limite de tokens para esta sessão. Por favor, tente novamente mais tarde."
    
    if st.session_state.request_count >= REQUEST_LIMIT:
        return "Você atingiu o limite de requisições para esta sessão. Por favor, tente novamente mais tarde."
    
    try:
        with st.spinner("Gerando conteúdo..."):
            # Atualizar o timestamp da última requisição
            st.session_state.last_request_time = time.time()
            
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
                "max_tokens": 4000  # Aumentado para respostas mais completas
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
                    'session_id': st.session_state.session_id
                })
                
                # Adicionar ao histórico
                st.session_state.history.append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'feature': st.session_state.current_feature,
                    'input': prompt[:100] + "..." if len(prompt) > 100 else prompt,  # Resumido para economizar espaço
                    'output': content,
                    'model': model,
                    'session_id': st.session_state.session_id
                })
                
                return content
            else:
                return f"Erro na API (Status {response.status_code}): {response.text}"
        
    except Exception as e:
        return f"Erro ao gerar conteúdo: {str(e)}"

# Função para análise de tom
def analyze_tone(text, target_audience, desired_impact):
    """
    Analisa o tom do texto e sugere melhorias baseadas no público-alvo
    e no impacto emocional desejado.
    
    Args:
        text (str): O texto a ser analisado
        target_audience (str): O público-alvo (cliente, equipe, executivos)
        desired_impact (str): O impacto desejado (tranquilizar, motivar, urgência)
        
    Returns:
        dict: Análise do tom e texto otimizado
    """
    if not st.session_state.api_key_configured or not st.session_state.api_key:
        return {
            'current_tone': "API não configurada",
            'emotional_impact': "Não foi possível analisar",
            'optimized_text': text
        }
    
    # Verificar limites
    if st.session_state.token_count >= TOKEN_LIMIT:
        return {
            'current_tone': "Limite de tokens atingido",
            'emotional_impact': "Não foi possível analisar",
            'optimized_text': text
        }
    
    if st.session_state.request_count >= REQUEST_LIMIT:
        return {
            'current_tone': "Limite de requisições atingido",
            'emotional_impact': "Não foi possível analisar",
            'optimized_text': text
        }
    
    try:
        with st.spinner("Analisando tom da comunicação..."):
            # Atualizar o timestamp da última requisição
            st.session_state.last_request_time = time.time()
            
            # Incrementar contador de requisições
            st.session_state.request_count += 1
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {st.session_state.api_key}"
            }
            
            prompt = f"""
            Analise o tom do seguinte texto destinado a '{target_audience}':
            
            "{text}"
            
            Forneça:
            1. Uma análise do tom atual (formal, informal, urgente, técnico, etc.)
            2. O provável impacto emocional no leitor
            3. Uma versão otimizada do texto para ter o impacto de '{desired_impact}'
            
            Retorne a resposta como um dicionário Python com as chaves: 'current_tone', 'emotional_impact', 'optimized_text'
            """
            
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "Você é um especialista em análise de comunicação e impacto emocional em contexto profissional."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 4000  # Aumentado para respostas mais completas
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                data=json.dumps(payload),
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result['choices'][0]['message']['content']
                
                # Atualizar contadores de tokens
                prompt_tokens = result['usage']['prompt_tokens']
                completion_tokens = result['usage']['completion_tokens']
                total_tokens = result['usage']['total_tokens']
                st.session_state.token_count += total_tokens
                
                # Registrar uso
                st.session_state.usage_data.append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'feature': "Análise de Tom",
                    'tokens': total_tokens,
                    'model': "gpt-3.5-turbo",
                    'session_id': st.session_state.session_id
                })
                
                # Tenta extrair o dicionário Python da resposta
                dict_pattern = r'\{.*\}'
                dict_match = re.search(dict_pattern, response_text, re.DOTALL)
                
                if dict_match:
                    dict_str = dict_match.group(0)
                    try:
                        # Substitui aspas simples por aspas duplas para compatibilidade com JSON
                        dict_str = dict_str.replace("'", "\"")
                        result = json.loads(dict_str)
                    except json.JSONDecodeError:
                        # Fallback se o parsing falhar
                        result = {
                            'current_tone': 'Não foi possível analisar precisamente',
                            'emotional_impact': 'Não foi possível analisar precisamente',
                            'optimized_text': text  # Mantém o texto original
                        }
                else:
                    # Se não puder extrair um dicionário, cria um resultado estruturado manualmente
                    lines = response_text.split('\n')
                    result = {
                        'current_tone': next((line.replace('1.', '').strip() for line in lines if '1.' in line), 'Não identificado'),
                        'emotional_impact': next((line.replace('2.', '').strip() for line in lines if '2.' in line), 'Não identificado'),
                        'optimized_text': text  # Default para o texto original
                    }
                    
                    # Tenta encontrar o texto otimizado
                    optimized_section = response_text.split('3.')
                    if len(optimized_section) > 1:
                        result['optimized_text'] = optimized_section[1].strip()
                
                return result
            else:
                return {
                    'current_tone': f"Erro na API (Status {response.status_code})",
                    'emotional_impact': "Não foi possível analisar",
                    'optimized_text': text
                }
                
    except Exception as e:
        return {
            'current_tone': f"Erro na análise: {str(e)}",
            'emotional_impact': "Não foi possível analisar",
            'optimized_text': text
        }

# Interface para análise de tom

def create_tone_analysis_section(content):
    """
    Cria a seção de análise de tom na interface
    
    Args:
        content (str): O texto gerado a ser analisado
        
    Returns:
        None: Atualiza a UI diretamente
    """
    st.markdown("## 🎭 Análise de Tom e Otimização")
    
    # Inicializar estado para os inputs se não existirem
    if 'tone_audience' not in st.session_state:
        st.session_state.tone_audience = "Cliente"
    if 'tone_impact' not in st.session_state:
        st.session_state.tone_impact = "Tranquilizar"
    if 'tone_analysis_result' not in st.session_state:
        st.session_state.tone_analysis_result = None
    
    with st.expander("Analisar e otimizar o tom da comunicação", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            target_audience = st.selectbox(
                "Público-alvo:",
                ["Cliente", "Equipe técnica", "Gerência", "Executivos", "Stakeholders", "Público geral"],
                key="tone_audience"
            )
        
        with col2:
            desired_impact = st.selectbox(
                "Impacto desejado:",
                ["Tranquilizar", "Motivar", "Gerar urgência", "Informar objetivamente", 
                 "Persuadir", "Demonstrar empatia", "Mostrar autoridade"],
                key="tone_impact"
            )
        
        # Usar um callback para análise de tom em vez de verificar clique de botão
        def analyze_tone_callback():
            with st.spinner("Analisando tom da comunicação..."):
                st.session_state.tone_analysis_result = analyze_tone(
                    content, 
                    st.session_state.tone_audience, 
                    st.session_state.tone_impact
                )
        
        st.button(
            "Analisar e otimizar tom", 
            key="analyze_tone_btn", 
            on_click=analyze_tone_callback
        )
        
        # Exibir resultados se disponíveis
        if st.session_state.tone_analysis_result:
            tone_analysis = st.session_state.tone_analysis_result
            
            st.markdown('<div class="tone-analysis-section">', unsafe_allow_html=True)
            
            st.markdown("### Análise do tom atual")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f'<div class="tone-current"><strong>Tom atual:</strong> {tone_analysis["current_tone"]}</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown(f'<div class="tone-current"><strong>Impacto emocional provável:</strong> {tone_analysis["emotional_impact"]}</div>', unsafe_allow_html=True)
            
            st.markdown("### Versão otimizada para o impacto desejado")
            st.markdown(f'<div class="tone-optimized">{tone_analysis["optimized_text"]}</div>', unsafe_allow_html=True)
            
            # Armazenar o texto otimizado na sessão
            st.session_state.optimized_content = tone_analysis["optimized_text"]
            
            col1, col2 = st.columns(2)
            with col1:
                # Download como texto
                st.download_button(
                    label="📄 Baixar versão otimizada (TXT)",
                    data=tone_analysis["optimized_text"],
                    file_name=f"comunicacao_otimizada_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
            
            with col2:
                # Download como DOCX
                docx_buffer = export_as_docx(tone_analysis["optimized_text"], "Comunicação Otimizada")
                st.download_button(
                    label="📝 Baixar versão otimizada (DOCX)",
                    data=docx_buffer,
                    file_name=f"comunicacao_otimizada_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            
            st.markdown('</div>', unsafe_allow_html=True)

# Função para exportar conteúdo como DOCX
def export_as_docx(content, filename="documento"):
    doc = docx.Document()
    
    # Adicionar título
    doc.add_heading(f"{filename}", 0)
    
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

    # ================= SIDEBAR =================

# Sidebar para configuração
with st.sidebar:
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    st.image("https://via.placeholder.com/150x150.png?text=NEXUS", width=150)
    
    # Mostrar status da API
    st.markdown("### Status")
    if st.session_state.api_key_configured:
        st.success("✅ API configurada automaticamente")
    else:
        st.error("❌ API não configurada. Contate o administrador.")
    
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
    st.caption("Esta é uma versão aprimorada do NEXUS com limites expandidos. Para uso sem limites, implemente o NEXUS em seu próprio ambiente.")

# ================= MAIN INTERFACE =================

# Interface principal
st.markdown('<h1 class="main-header">NEXUS</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Comunicação de projetos clara, eficaz e profissional</p>', unsafe_allow_html=True)

# Mensagem sobre versão aprimorada
st.info(f"""
**Versão NEXUS Aprimorada**
Esta versão do NEXUS possui limites expandidos para melhor experiência:
- Até {REQUEST_LIMIT} requisições por sessão
- Até {TOKEN_LIMIT} tokens por sessão
- Respostas mais detalhadas e completas
- Sem espera entre requisições
""")

# Histórico de gerações recentes
if st.session_state.history:
    with st.expander("Histórico de Gerações Recentes", expanded=False):
        for i, item in enumerate(reversed(st.session_state.history[-5:])):  # Ampliado para 5 itens mais recentes
            st.markdown(f"**{item['timestamp']} - {item['feature']}**")
            if st.button(f"Carregar este conteúdo ↩️", key=f"load_{i}"):
                st.session_state.current_feature = item['feature']
                st.session_state.generated_content = item['output']
                st.experimental_rerun()
            st.markdown("---")

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
    else:
        with col2:
            with st.expander(f"{details['icon']} {feature}", expanded=False):
                st.markdown(f"**{details['description']}**")
                if st.button(f"Usar {feature}", key=f"select_{feature}"):
                    st.session_state.current_feature = feature
    count += 1

    # ================= FEATURE INTERFACE =================

# Se uma funcionalidade foi selecionada na sessão atual ou anteriormente
if st.session_state.current_feature:
    current_feature = st.session_state.current_feature
    feature_details = feature_options[current_feature]
    
    st.markdown(f"## {feature_details['icon']} {current_feature}")
    
    # Verificar limites antes de mostrar a interface (sem verificar tempo entre requisições)
    if st.session_state.token_count >= TOKEN_LIMIT:
        st.error(f"Você atingiu o limite de {TOKEN_LIMIT} tokens para esta sessão. Por favor, tente novamente mais tarde.")
    elif st.session_state.request_count >= REQUEST_LIMIT:
        st.error(f"Você atingiu o limite de {REQUEST_LIMIT} requisições para esta sessão. Por favor, tente novamente mais tarde.")
    else:
        # Interface específica da funcionalidade
        with st.form(key=f"{current_feature}_form"):
            st.markdown(f"**{feature_details['description']}**")
            
            # Campo de subtipo
            subtype = st.selectbox("Tipo de Comunicação", feature_details['subtypes'])
            
            # Campos comuns a todas as funcionalidades (exceto PMBOK que tem campos específicos)
            if current_feature != "Consultor PMBOK 7":
                context = st.text_area("Contexto do Projeto", 
                                    help="Descreva o projeto, fase atual e informações relevantes",
                                    height=100,
                                    placeholder="Ex: Projeto de desenvolvimento do aplicativo mobile, fase de testes")
            
            # Campos específicos por funcionalidade
            prompt = ""
            
            if current_feature == "Gerador de Comunicações Estruturadas":
                audience = st.text_input("Público-alvo", 
                                    help="Para quem esta comunicação será enviada (equipe, cliente, stakeholder)",
                                    placeholder="Ex: Cliente, diretor de marketing da empresa XYZ")
                key_points = st.text_area("Pontos-chave", 
                                        help="Liste os principais pontos que devem ser incluídos na comunicação",
                                        height=150,
                                        placeholder="Ex: Atraso de 3 dias devido a bugs na integração; Plano de recuperação com recursos adicionais")
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
                                        height=100,
                                        placeholder="Ex: João Silva (Gerente de Projeto), Maria Costa (Desenvolvedora Frontend)")
                topics = st.text_area("Tópicos a serem abordados", 
                                    help="Liste os tópicos que precisam ser discutidos",
                                    height=150,
                                    placeholder="Ex: Atualização do cronograma, Bugs pendentes, Feedback do cliente")
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
                                        height=100,
                                        placeholder="Ex: Aprovação do novo design, Extensão do prazo em 1 semana")
                    actions = st.text_area("Ações acordadas", 
                                        help="Liste as ações acordadas, responsáveis e prazos",
                                        height=100,
                                        placeholder="Ex: João irá corrigir o bug #123 até amanhã, Maria criará novos componentes até sexta")
                    
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
                                                placeholder="Ex: Definidas as prioridades para o próximo sprint e resolvidos os bloqueios atuais")
                    action_items = st.text_area("Itens de ação", 
                                            help="Liste os itens de ação, responsáveis e prazos",
                                            height=100,
                                            placeholder="Ex: João: revisão de código até 25/03; Maria: implementação da nova feature até 27/03")
                    
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
                                            placeholder="Ex: A implementação do Redux utiliza reducers imutáveis para gerenciar o estado global da aplicação...")
                audience = st.selectbox("Público-alvo", 
                                    ["Executivos", "Clientes não-técnicos", "Equipe de Negócios", "Equipe Técnica Junior"])
                key_concepts = st.text_input("Conceitos-chave a preservar", 
                                        help="Liste conceitos técnicos que devem ser mantidos mesmo se simplificados",
                                        placeholder="Ex: gerenciamento de estado, API, front-end")
                
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
                Forneça uma explicação completa e detalhada, com exemplos e analogias apropriadas para o público.
                """
                
            elif current_feature == "Facilitador de Feedback":
                situation = st.text_area("Situação", 
                                    help="Descreva a situação específica para a qual você precisa fornecer feedback",
                                    height=150,
                                    placeholder="Ex: Atraso na entrega de componentes para o projeto principal...")
                strengths = st.text_area("Pontos Fortes", 
                                    help="Liste aspectos positivos que devem ser destacados",
                                    height=100,
                                    placeholder="Ex: Qualidade do código entregue, comunicação proativa de desafios")
                areas_for_improvement = st.text_area("Áreas para Melhoria", 
                                                help="Liste aspectos que precisam ser melhorados",
                                                height=100,
                                                placeholder="Ex: Estimativas de tempo irrealistas, falha em pedir ajuda quando bloqueado")
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
                
                Formate como um roteiro/script detalhado que o usuário pode seguir na conversa ou adaptar para uma comunicação escrita.
                Adicione observações e dicas de comunicação não-verbal quando relevante.
                """
                
            elif current_feature == "Detector de Riscos de Comunicação":
                content_to_analyze = st.text_area("Conteúdo para Análise", 
                                                help="Cole aqui o texto que você deseja analisar quanto a riscos de comunicação",
                                                height=200,
                                                placeholder="Ex: Devido a circunstâncias imprevistas no desenvolvimento, alguns recursos podem sofrer atrasos...")
                audience = st.text_input("Público-alvo", 
                                    help="Descreva quem receberá esta comunicação",
                                    placeholder="Ex: Cliente executivo com pouco conhecimento técnico")
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
                6. Analisar a estrutura geral e propor melhorias organizacionais
                7. Verificar se há informações críticas ausentes
                
                Organize sua análise em forma de tabela com colunas para: Trecho problemático, Risco potencial, Sugestão de melhoria.
                Ao final, forneça uma avaliação geral dos riscos de comunicação (Baixo/Médio/Alto) e um resumo das principais recomendações.
                Forneça também uma versão revisada completa do texto.
                """
                
            elif current_feature == "Consultor PMBOK 7":
                pmbok_topic = subtype  # Já definido pelo selectbox de subtypes
                
                project_context = st.text_area("Contexto do Projeto", 
                                        help="Descreva brevemente o projeto ou a situação para contextualizar sua dúvida",
                                        height=100,
                                        placeholder="Ex: Estamos iniciando um projeto de desenvolvimento de software com metodologia híbrida...")
                
                specific_question = st.text_area("Sua Dúvida Específica", 
                                            help="Detalhe sua dúvida ou o que você precisa saber sobre o tema selecionado",
                                            height=150,
                                            placeholder="Ex: Como aplicar os princípios de valor do PMBOK 7 em um ambiente que tradicionalmente usava metodologias em cascata?")
                
                experience_level = st.select_slider("Seu Nível de Experiência", 
                                                options=["Iniciante", "Intermediário", "Avançado", "Especialista"],
                                                value="Intermediário")
                
                organization_context = st.text_input("Contexto Organizacional", 
                                                help="Descreva brevemente o contexto organizacional (opcional)",
                                                placeholder="Ex: Empresa de médio porte do setor financeiro com cultura tradicional")
                
                base_prompt = f"""
                Forneça uma orientação detalhada sobre o tema "{pmbok_topic}" do PMBOK 7 com base nas seguintes informações:
                
                Contexto do Projeto: {project_context}
                Dúvida Específica: {specific_question}
                Nível de Experiência do Usuário: {experience_level}
                Contexto Organizacional: {organization_context}
                
                Sua resposta deve:
                1. Explicar os conceitos relevantes do PMBOK 7 relacionados à dúvida
                2. Fornecer orientações práticas adaptadas ao contexto específico
                3. Apresentar exemplos concretos de aplicação
                4. Destacar boas práticas e recomendações
                5. Considerar o nível de experiência do usuário ({experience_level})
                6. Fazer conexões com outros domínios ou princípios relevantes do PMBOK 7
                7. Incluir dicas de implementação prática
                8. Mencionar possíveis desafios e como superá-los
                
                Formate a resposta de maneira estruturada, com seções claras e, se apropriado, inclua referências aos elementos específicos do PMBOK 7.
                """
                
                # Enriquecemos o prompt com informações relevantes do PMBOK 7
                prompt = enrich_pmbok_prompt(base_prompt, pmbok_topic)
            
            submit_button = st.form_submit_button(f"Gerar {current_feature}")
        
        if submit_button:
            if not st.session_state.api_key_configured:
                st.error("API não configurada. Por favor, contate o administrador.")
            elif st.session_state.token_count >= TOKEN_LIMIT:
                st.error(f"Você atingiu o limite de {TOKEN_LIMIT} tokens para esta sessão. Por favor, tente novamente mais tarde.")
            elif st.session_state.request_count >= REQUEST_LIMIT:
                st.error(f"Você atingiu o limite de {REQUEST_LIMIT} requisições para esta sessão. Por favor, tente novamente mais tarde.")
            else:
                # Gerar conteúdo
                generated_content = generate_content(prompt, model="gpt-3.5-turbo", temperature=0.7)
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
                
                # Análise de Tom (para todos os tipos de conteúdo exceto PMBOK)
                if current_feature != "Consultor PMBOK 7":
                    create_tone_analysis_section(generated_content)
                
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

Este aplicativo é uma versão aprimorada do NEXUS, um assistente de IA para comunicação e gerenciamento de projetos. Foi criado como parte do artigo "**Comunicação eficiente em projetos: como a IA pode ajudar gerentes e equipes**".

#### Recursos do NEXUS:
- **Gerador de Comunicações**: E-mails, relatórios e comunicados adaptados ao seu contexto
- **Assistente de Reuniões**: Agendas, atas e follow-ups estruturados
- **Tradutor de Jargão**: Simplificação de linguagem técnica para diferentes públicos
- **Facilitador de Feedback**: Estruturação de feedback construtivo e equilibrado
- **Detector de Riscos**: Análise de comunicações para evitar mal-entendidos
- **Consultor PMBOK 7**: Orientações sobre gerenciamento de projetos segundo o PMBOK 7
- **Análise de Tom**: Otimização do impacto emocional de suas comunicações

Para implementar o NEXUS em seu próprio ambiente:
1. Acesse o código-fonte no GitHub: [github.com/seu-usuario/nexus-assistant](https://github.com/seu-usuario/nexus-assistant)
2. Siga as instruções de instalação no README
3. Configure com sua própria chave API da OpenAI
4. Personalize para as necessidades específicas da sua equipe

**Experimente as seis funcionalidades principais do NEXUS e veja como a IA pode transformar a comunicação nos seus projetos!**
""")

# Rodapé com créditos
st.markdown("""
<div style="text-align: center; color: gray; font-size: 0.8rem;">
    NEXUS | Assistente de Comunicação e Gerenciamento de Projetos | © 2025
</div>
""", unsafe_allow_html=True)


                      
