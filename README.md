## Lincer Agent

Lincehub - Analise de vistorias com IA para ambientes de Construcao, Varejo e Industria utilizando o modelo multimodal Gemini 2.5 do Google.

### Funcionalidades

- **Vistoria multi-perfil**: Construcao, Loja de varejo, Planta industrial
- **Relatorios JSON estruturados** com problemas, severidade, timestamps e acoes recomendadas
- **Extracao de transcricao completa** do audio do video
- **Avaliacao de risco** com classificacao de nivel de risco geral
- **Relatorios para download** (JSON + transcricao)
- Suporte para formatos de video MP4, MOV, AVI, WebM

### Como Comecar

1. Clone o repositorio:

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/starter_ai_agents/multimodal_ai_agent
```

2. Crie o ambiente virtual e instale as dependencias:

```bash
uv venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

3. Obtenha sua chave API do Google Gemini em [Google AI Studio](https://aistudio.google.com/apikey)

4. Configure sua chave API (escolha um metodo):

```bash
# Opcao A: Variavel de ambiente
export GEMINI_API_KEY=sua_chave_api_aqui

# Opcao B: Inserir diretamente na barra lateral do app
```

5. Execute o aplicativo Streamlit:

```bash
streamlit run mutimodal_agent.py
```

### Deploy no Streamlit Cloud

1. Faca push do seu codigo para o GitHub

2. Acesse [share.streamlit.io](https://share.streamlit.io)

3. Conecte seu repositorio do GitHub

4. Defina o caminho do arquivo principal: `starter_ai_agents/multimodal_ai_agent/mutimodal_agent.py`

5. Adicione seu segredo em **Configuracoes avancadas > Secrets**:
   ```toml
   GEMINI_API_KEY = "sua-chave-api-aqui"
   ```

6. Clique em Deploy!

### Esquema do Relatorio JSON

O relatorio de vistoria segue esta estrutura:

```json
{
  "resumo": "Avaliacao geral breve",
  "nivel_risco_geral": "BAIXO | MEDIO | ALTO | CRITICO",
  "problemas": [
    {
      "id": "PRB-001",
      "timestamp_inicio": "HH:MM:SS",
      "timestamp_fim": "HH:MM:SS",
      "categoria": "SEGURANCA | QUALIDADE | ORGANIZACAO | CONFORMIDADE | OUTRO",
      "titulo": "Titulo do problema",
      "descricao": "Descricao detalhada",
      "severidade": "BAIXO | MEDIO | ALTO | CRITICO",
      "acao_recomendada": "O que fazer",
      "norma_ou_regra": "Regulamentacao relevante"
    }
  ],
  "proximas_acoes": [
    {
      "responsavel": "Supervisor | Gerente de Loja | Engenheiro de Seguranca | Outro",
      "acao": "Acao especifica",
      "prioridade": "BAIXA | MEDIA | ALTA",
      "prazo_em_dias": 7
    }
  ],
  "transcricao_completa": "Texto completo da transcricao"
}
```

### Perfis de Vistoria

- **Construcao**: EPI, andaimes, riscos de queda, armazenamento de materiais, maquinario, seguranca eletrica
- **Loja de varejo**: Conformidade com planograma, limpeza, corredores bloqueados, sinalizacao, organizacao de filas
- **Planta industrial**: Bloqueio/etiquetagem, protecao de maquinas, comportamento do operador, fluxo de materiais, ergonomia
