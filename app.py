# Lincer Agent - Lincehub app para vistorias
# Configure GEMINI_API_KEY nos secrets do Streamlit Cloud ou como variavel de ambiente
# Execute com: streamlit run app.py

import streamlit as st
from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.models.google import Gemini
from agno.media import Video
from pathlib import Path
import tempfile
import json
import os
import re

st.set_page_config(
    page_title="Lincer Agent",
    page_icon="L",
    layout="wide"
)

# Obtem chave API do secrets ou variavel de ambiente
def get_api_key() -> str:
    """Obtem a chave API do Gemini dos secrets ou variavel de ambiente."""
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return os.environ.get("GEMINI_API_KEY", "")

GEMINI_API_KEY = get_api_key()

# Prompts especificos por perfil de vistoria
PROFILE_PROMPTS = {
    "Construcao": """Foque sua vistoria em:
- Equipamentos de Protecao Individual (EPI): capacetes, coletes refletivos, luvas, oculos de seguranca, botinas
- Protecao contra quedas: seguranca de andaimes, guarda-corpos, redes de protecao, uso de cinto de seguranca
- Armazenamento de materiais: empilhamento adequado, armazenamento seguro, manuseio de materiais perigosos
- Maquinario e equipamentos: operacao correta, protecoes de seguranca, condicoes de manutencao
- Organizacao e limpeza: entulho, riscos de tropecos, passagens livres
- Seguranca em escavacoes: escoramento, taludes, acesso e saida
- Seguranca eletrica: fiacoes expostas, aterramento adequado, bloqueio e etiquetagem""",
    
    "Loja de varejo": """Foque sua vistoria em:
- Conformidade com planograma: posicionamento de produtos, organizacao de prateleiras, frente de gondola
- Limpeza da loja: pisos, prateleiras, displays, banheiros
- Seguranca de corredores: passagens bloqueadas, riscos de tropecos, derramamentos
- Sinalizacao: precisao de precos, displays promocionais, placas de seguranca
- Organizacao de filas: fluxo de caixa, areas de espera
- Saidas de emergencia: caminhos livres, sinalizacao adequada, acessibilidade
- Estoque: excesso, falta, produtos danificados
- Experiencia do cliente: disponibilidade de funcionarios, qualidade do atendimento""",
    
    "Planta industrial": """Foque sua vistoria em:
- Bloqueio e Etiquetagem (LOTO): procedimentos adequados, isolamento de energia
- Protecao de maquinas: barreiras de seguranca, intertravamentos, paradas de emergencia
- Comportamento do operador: postura, uso de EPI, praticas seguras de trabalho
- Fluxo de materiais: seguranca de esteiras, operacoes de empilhadeira, carga/descarga
- Manuseio de produtos quimicos: armazenamento adequado, rotulagem, contencao de derramamentos
- Ventilacao: extracao de fumos, qualidade do ar
- Exposicao ao ruido: protecao auditiva, barreiras acusticas
- Ergonomia: configuracao de estacoes de trabalho, riscos de movimentos repetitivos"""
}

JSON_SCHEMA = """{
  "resumo": "Avaliacao geral breve da vistoria",
  "nivel_risco_geral": "BAIXO | MEDIO | ALTO | CRITICO",
  "problemas": [
    {
      "id": "identificador unico como PRB-001",
      "timestamp_inicio": "HH:MM:SS",
      "timestamp_fim": "HH:MM:SS", 
      "categoria": "SEGURANCA | QUALIDADE | ORGANIZACAO | CONFORMIDADE | OUTRO",
      "titulo": "Titulo curto do problema",
      "descricao": "Descricao detalhada do problema",
      "severidade": "BAIXO | MEDIO | ALTO | CRITICO",
      "acao_recomendada": "O que deve ser feito para corrigir",
      "norma_ou_regra": "Regulamentacao ou norma relevante se aplicavel"
    }
  ],
  "proximas_acoes": [
    {
      "responsavel": "Supervisor | Gerente de Loja | Engenheiro de Seguranca | Outro",
      "acao": "Acao especifica a ser tomada",
      "prioridade": "BAIXA | MEDIA | ALTA",
      "prazo_em_dias": numero
    }
  ],
  "transcricao_completa": "Transcricao completa de toda fala e eventos relevantes observados"
}"""


def build_inspection_prompt(profile: str, extra_context: str | None) -> str:
    """Constroi o prompt completo de vistoria para o Gemini."""
    profile_instructions = PROFILE_PROMPTS.get(profile, PROFILE_PROMPTS["Construcao"])
    
    prompt = f"""Voce e um assistente especialista em vistorias e auditorias especializado em ambientes de {profile}.

TAREFA: Analise este video minuciosamente e produza um relatorio de vistoria abrangente.

{profile_instructions}

INSTRUCOES:
1. Assista ao video inteiro com atencao, anotando todos os timestamps onde ocorrem problemas
2. Transcreva toda fala relevante, conversas e narracoes
3. Identifique TODOS os riscos de seguranca, problemas de qualidade, violacoes de conformidade e areas de preocupacao
4. Classifique cada problema por severidade e forneca recomendacoes acionaveis
5. Avalie o nivel de risco geral com base nas descobertas cumulativas

{"CONTEXTO ADICIONAL DO USUARIO: " + extra_context if extra_context else ""}

FORMATO DE SAIDA:
Retorne sua resposta como JSON valido seguindo exatamente este esquema:
{JSON_SCHEMA}

IMPORTANTE:
- Seja minucioso - nao deixe passar nenhum problema visivel no video
- Forneca timestamps especificos para cada problema
- Inclua a transcricao completa em transcricao_completa
- Se nenhum problema for encontrado, retorne um array de problemas vazio com um resumo positivo
- Garanta que todo o JSON esteja formatado corretamente e valido
- RESPONDA SEMPRE EM PORTUGUES BRASILEIRO"""

    return prompt


def parse_json_response(response_text: str) -> dict | None:
    """Extrai e analisa JSON da resposta do Gemini."""
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    
    json_match = re.search(r'\{[\s\S]*\}', response_text)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    return None


def get_severity_color(severity: str) -> str:
    """Retorna indicador para nivel de severidade."""
    colors = {
        "BAIXO": "[BAIXO]",
        "MEDIO": "[MEDIO]", 
        "ALTO": "[ALTO]",
        "CRITICO": "[CRITICO]",
        "LOW": "[BAIXO]",
        "MEDIUM": "[MEDIO]",
        "HIGH": "[ALTO]",
        "CRITICAL": "[CRITICO]"
    }
    return colors.get(severity.upper(), "[--]")


def get_risk_badge(risk_level: str) -> str:
    """Retorna badge para nivel de risco."""
    badges = {
        "BAIXO": "RISCO BAIXO",
        "MEDIO": "RISCO MEDIO",
        "ALTO": "RISCO ALTO",
        "CRITICO": "RISCO CRITICO",
        "LOW": "RISCO BAIXO",
        "MEDIUM": "RISCO MEDIO",
        "HIGH": "RISCO ALTO",
        "CRITICAL": "RISCO CRITICO"
    }
    return badges.get(risk_level.upper(), risk_level)


def get_risk_color(risk_level: str) -> str:
    """Retorna cor CSS para nivel de risco."""
    colors = {
        "BAIXO": "#28a745",
        "MEDIO": "#ffc107",
        "ALTO": "#fd7e14",
        "CRITICO": "#dc3545",
        "LOW": "#28a745",
        "MEDIUM": "#ffc107",
        "HIGH": "#fd7e14",
        "CRITICAL": "#dc3545"
    }
    return colors.get(risk_level.upper(), "#6c757d")


# UI Principal
st.title("Lincer Agent")
st.markdown("*Lincehub - Analise de vistorias com IA para Construcao, Varejo e Industria*")

# Verifica se a API key esta configurada
if not GEMINI_API_KEY:
    st.error("Chave API Gemini nao configurada. Configure GEMINI_API_KEY nos secrets do Streamlit ou como variavel de ambiente.")
    st.stop()

# Configuracao na barra lateral
with st.sidebar:
    st.header("Configuracoes da Vistoria")
    
    profile = st.selectbox(
        "Perfil de Vistoria",
        options=["Construcao", "Loja de varejo", "Planta industrial"],
        help="Selecione o tipo de ambiente sendo vistoriado"
    )
    
    extra_context = st.text_area(
        "Contexto Adicional (opcional)",
        placeholder="Ex: 'Foque na area de carga e descarga' ou 'Esta e uma vistoria de acompanhamento'",
        help="Forneca instrucoes ou contexto especifico para a vistoria"
    )

# Area de conteudo principal
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Enviar Video")
    uploaded_file = st.file_uploader(
        "Selecione o arquivo de video",
        type=['mp4', 'mov', 'avi', 'webm'],
        help="Formatos suportados: MP4, MOV, AVI, WebM"
    )
    
    if uploaded_file:
        st.video(uploaded_file)
        st.caption(f"Arquivo: {uploaded_file.name} ({uploaded_file.size / (1024*1024):.1f} MB)")

with col2:
    st.subheader("Resultados da Analise")
    
    if not uploaded_file:
        st.info("Envie um arquivo de video para iniciar a analise de vistoria.")
    else:
        analyze_btn = st.button("Analisar Video", type="primary", use_container_width=True)
        
        if analyze_btn:
            agent = Agent(
                name="Lincer Inspector",
                model=Gemini(id="gemini-2.5-flash", api_key=GEMINI_API_KEY),
                markdown=True,
            )
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                tmp_file.write(uploaded_file.read())
                video_path = tmp_file.name
            
            try:
                with st.spinner("Analisando video... Isso pode levar alguns minutos para videos mais longos."):
                    video = Video(filepath=video_path)
                    prompt = build_inspection_prompt(profile, extra_context)
                    result: RunOutput = agent.run(prompt, videos=[video])
                
                st.session_state['inspection_result'] = result.content
                st.session_state['parsed_json'] = parse_json_response(result.content)
                
            except Exception as e:
                st.error(f"Falha na analise: {str(e)}")
            finally:
                Path(video_path).unlink(missing_ok=True)

# Exibe resultados se disponiveis
if 'inspection_result' in st.session_state:
    parsed = st.session_state.get('parsed_json')
    
    if parsed:
        st.divider()
        col_sum, col_risk = st.columns([3, 1])
        
        with col_sum:
            st.markdown("### Resumo")
            summary = parsed.get('resumo') or parsed.get('summary', 'Resumo nao disponivel')
            st.write(summary)
        
        with col_risk:
            risk_level = parsed.get('nivel_risco_geral') or parsed.get('overall_risk_level', 'DESCONHECIDO')
            risk_color = get_risk_color(risk_level)
            st.markdown("### Nivel de Risco")
            st.markdown(f"""
                <div style="background-color: {risk_color}; color: white; padding: 10px 20px; 
                border-radius: 8px; text-align: center; font-weight: bold; font-size: 1.1em;">
                {get_risk_badge(risk_level)}
                </div>
            """, unsafe_allow_html=True)
        
        issues = parsed.get('problemas') or parsed.get('issues', [])
        if issues:
            st.divider()
            st.markdown(f"### Problemas Encontrados ({len(issues)})")
            
            issues_data = []
            for issue in issues:
                severity = issue.get('severidade') or issue.get('severity', '')
                issues_data.append({
                    "Severidade": f"{get_severity_color(severity)}",
                    "Horario": f"{issue.get('timestamp_inicio') or issue.get('timestamp_start', '')} - {issue.get('timestamp_fim') or issue.get('timestamp_end', '')}",
                    "Categoria": issue.get('categoria') or issue.get('category', ''),
                    "Titulo": issue.get('titulo') or issue.get('title', ''),
                    "Acao": issue.get('acao_recomendada') or issue.get('recommended_action', '')
                })
            
            st.dataframe(issues_data, use_container_width=True, hide_index=True)
            
            with st.expander("Descricoes Detalhadas dos Problemas"):
                for issue in issues:
                    issue_id = issue.get('id', '')
                    issue_title = issue.get('titulo') or issue.get('title', '')
                    st.markdown(f"**{issue_id} - {issue_title}**")
                    st.write(issue.get('descricao') or issue.get('description', ''))
                    standard = issue.get('norma_ou_regra') or issue.get('standard_or_rule')
                    if standard:
                        st.caption(f"Norma: {standard}")
                    st.divider()
        else:
            st.success("Nenhum problema encontrado nesta vistoria!")
        
        next_actions = parsed.get('proximas_acoes') or parsed.get('next_actions', [])
        if next_actions:
            st.divider()
            st.markdown("### Proximas Acoes Recomendadas")
            for i, action in enumerate(next_actions, 1):
                priority = action.get('prioridade') or action.get('priority', 'MEDIA')
                priority_map = {"BAIXA": "[BAIXA]", "MEDIA": "[MEDIA]", "ALTA": "[ALTA]", 
                               "LOW": "[BAIXA]", "MEDIUM": "[MEDIA]", "HIGH": "[ALTA]"}
                priority_text = priority_map.get(priority.upper(), "[--]")
                owner = action.get('responsavel') or action.get('owner', 'A definir')
                action_text = action.get('acao') or action.get('action', '')
                due_days = action.get('prazo_em_dias') or action.get('due_in_days', '?')
                st.markdown(f"{i}. {priority_text} **{owner}**: {action_text} *(Prazo: {due_days} dias)*")
        
        st.divider()
        col_dl1, col_dl2 = st.columns(2)
        
        with col_dl1:
            st.download_button(
                "Baixar Relatorio JSON",
                data=json.dumps(parsed, indent=2, ensure_ascii=False),
                file_name="relatorio_vistoria.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col_dl2:
            transcript = parsed.get('transcricao_completa') or parsed.get('raw_transcript', 'Transcricao nao disponivel')
            st.download_button(
                "Baixar Transcricao",
                data=transcript,
                file_name="transcricao.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with st.expander("Resposta JSON Completa"):
            st.json(parsed)
        
        with st.expander("Transcricao Completa"):
            st.text(parsed.get('transcricao_completa') or parsed.get('raw_transcript', 'Transcricao nao disponivel'))
    
    else:
        st.warning("Nao foi possivel extrair JSON estruturado da resposta. Exibindo saida bruta:")
        st.markdown(st.session_state['inspection_result'])
        
        st.download_button(
            "Baixar Resposta Bruta",
            data=st.session_state['inspection_result'],
            file_name="resposta_vistoria.txt",
            mime="text/plain"
        )

st.divider()
st.caption("Desenvolvido com Streamlit e Google Gemini 2.5 | Lincehub - Analise de vistorias com IA")
