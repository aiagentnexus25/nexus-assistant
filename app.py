import streamlit as st
import json

# Configuração básica da página
st.set_page_config(page_title="NEXUS - Verificação de Configuração", page_icon="🔧")

st.title("NEXUS - Verificação de Configuração")
st.write("Este aplicativo verifica se os segredos estão configurados corretamente.")

# Tentar acessar segredos de diferentes maneiras
try:
    # Método 1: Acesso direto via st.secrets
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
        masked_key = api_key[:5] + "..." + api_key[-4:] if len(api_key) > 10 else "***"
        st.success(f"✅ Segredo encontrado via st.secrets['OPENAI_API_KEY']: {masked_key}")
    else:
        st.error("❌ Segredo 'OPENAI_API_KEY' não encontrado no st.secrets")
    
    # Método 2: Listar todos os segredos disponíveis (sem mostrar valores)
    st.subheader("Segredos disponíveis:")
    secret_keys = list(st.secrets.keys())
    st.write(f"Chaves encontradas: {secret_keys}")
    
    # Método 3: Tentar acessar via get
    api_key_get = st.secrets.get("OPENAI_API_KEY", "NÃO ENCONTRADO")
    if api_key_get != "NÃO ENCONTRADO":
        masked_key_get = api_key_get[:5] + "..." + api_key_get[-4:] if len(api_key_get) > 10 else "***"
        st.success(f"✅ Segredo encontrado via st.secrets.get(): {masked_key_get}")
    else:
        st.error("❌ Segredo não encontrado via método get()")
    
    # Verificar o formato do segredo
    if "OPENAI_API_KEY" in st.secrets:
        prefix = api_key[:8] if len(api_key) > 8 else api_key
        st.write(f"Prefixo da chave: {prefix}")
        
        if prefix.startswith("sk-"):
            st.success("✅ Formato da chave parece correto (começa com 'sk-')")
        else:
            st.warning("⚠️ Formato da chave pode estar incorreto (não começa com 'sk-')")
    
except Exception as e:
    st.error(f"Erro ao acessar segredos: {type(e).__name__}: {str(e)}")

st.write("---")
st.caption("Esta é uma ferramenta de diagnóstico para o NEXUS.")
