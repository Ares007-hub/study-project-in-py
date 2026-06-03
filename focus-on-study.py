import time
import json
import os
from datetime import datetime
import pyautogui
import pandas as pd
import matplotlib.pyplot as plt
import pyperclip

# Configurações globais
DATA_FILE = "historico_estudos.json"

# Palavras-chave que DEVEM estar no título da janela para o cronômetro rodar
TERMOS_PERMITIDOS = ["metodooba", "mentoria", "duckduckgo", "oba"]

# Tenta importar o gerenciador de janelas (focado em Windows)
try:
    import pygetwindow as gw
    WINDOWS_OS = True
except ImportError:
    WINDOWS_OS = False

# --- FUNÇÕES DE BANCO DE DADOS (JSON) ---
def carregar_dados():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("[AVISO] Erro ao ler o arquivo de histórico. Criando um novo.")
            return []
    return []

def salvar_dados(dados):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# --- VALIDATÓRIOS DE ENTRADA ---
def obter_input_float(mensagem, minimo=0.1):
    while True:
        try:
            valor = float(input(mensagem))
            if valor >= minimo:
                return valor
            print(f"[ERRO] Por favor, insira um valor maior ou igual a {minimo}.")
        except ValueError:
            print("[ERRO] Entrada inválida. Digite um número válido.")

def obter_input_int(mensagem, minimo=0, maximo=10):
    while True:
        try:
            valor = int(input(mensagem))
            if minimo <= valor <= maximo:
                return valor
            print(f"[ERRO] Por favor, insira um número entre {minimo} e {maximo}.")
        except ValueError:
            print("[ERRO] Entrada inválida. Digite um número inteiro.")

# --- DETECTOR DE TELA CHEIA E SITE ESPECÍFICO ---
def verificar_tela_cheia():
    """Detecta se a janela ativa e do site correto E ocupa a resolucao do monitor com margem para a barra"""
    if not WINDOWS_OS:
        return True 
    try:
        j_ativa = gw.getActiveWindow()
        if j_ativa and j_ativa.title:
            largura_tela, altura_tela = pyautogui.size()
            
            # Da uma colher de cha de 50 pixels para baixo caso a barra do Windows esteja aparecendo
            dimensao_ok = j_ativa.width >= largura_tela and j_ativa.height >= (altura_tela - 50)
            
            titulo_janela = j_ativa.title.lower()
            
            # Se for o menu de alternancia do Windows, mantem o status anterior para nao computar erro falso
            if "alternância de tarefas" in titulo_janela or "task switching" in titulo_janela:
                return True
                
            site_ok = any(termo in titulo_janela for termo in TERMOS_PERMITIDOS)
            
            return dimensao_ok and site_ok
    except Exception:
        pass
    return False

# --- GERADOR DE GRÁFICOS ---
def gerar_grafico_evolucao(materia_alvo, df_materia):
    if len(df_materia) < 1:
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(f"Analise de Desempenho Historico: {materia_alvo.upper()}", fontsize=14, fontweight='bold')

    # Gráfico 1: Evolução dos Acertos
    ax1.plot(df_materia['data'], df_materia['acertos'], marker='o', color='#2ca02c', linewidth=2, label='Acertos')
    ax1.axhline(y=7, color='r', linestyle='--', alpha=0.6, label='Meta (70%)')
    ax1.set_title("Evolucao de Acertos (Max: 10)")
    ax1.set_xlabel("Data da Sessao")
    ax1.set_ylabel("Questoes Acertadas")
    ax1.set_ylim(-0.5, 10.5)
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Gráfico 2: Tempo Focado vs Tempo Perdido
    df_materia_minutos = df_materia.copy()
    df_materia_minutos['min_estudados'] = df_materia_minutos['tempo_estudado_s'] / 60
    df_materia_minutos['min_perdidos'] = df_materia_minutos['tempo_perdido_s'] / 60

    x = range(len(df_materia))
    ax2.bar(x, df_materia_minutos['min_estudados'], width=0.4, label='Tempo Focado (min)', color='#1f77b4', align='center')
    ax2.bar(x, df_materia_minutos['min_perdidos'], width=0.4, label='Tempo Perdido (min)', color='#d62728', align='edge')
    ax2.set_title("Tempo Focado vs Distracoes")
    ax2.set_xlabel("Sessoes (Ordem Cronologica)")
    ax2.set_ylabel("Minutos")
    ax2.set_xticks(x)
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    plt.tight_layout()
    nome_arquivo = f"performance_{materia_alvo.lower().replace(' ', '_')}.png"
    plt.savefig(nome_arquivo)
    plt.close()
    print(f"[INFO] Grafico de evolucao atualizado e salvo como: '{nome_arquivo}'")

# --- DASHBOARD TEXTUAL ---
def exibir_dashboard(materia_alvo):
    dados = carregar_dados()
    if not dados:
        print("[AVISO] Sem dados historicos para exibir.")
        return
    
    df = pd.DataFrame(dados)
    df_materia = df[df['materia'].str.lower() == materia_alvo.lower()]
    
    if df_materia.empty:
        print(f"[AVISO] Nenhuma sessao anterior encontrada para a materia: {materia_alvo}")
        return
    
    print(f"\n" + "="*20 + f" DASHBOARD HISTORICO: {materia_alvo.upper()} " + "="*20)
    print(f"Total de sessoes realizadas: {len(df_materia)}")
    print(f"Tempo medio estudando:       {df_materia['tempo_estudado_s'].mean() / 60:.1f} minutos")
    print(f"Total de distracoes flagradas:{df_materia['distracoes'].sum()} vezes")
    print(f"Tempo total desperdicado:    {df_materia['tempo_perdido_s'].sum() / 60:.1f} minutos")
    
    print("\n" + "-"*15 + " PERFORMANCE NOS SIMULADOS (MAX: 10) " + "-"*15)
    print(f"Media de acertos atual:      {df_materia['acertos'].mean():.1f}")
    print(f"Melhor pontuacao historica:  {df_materia['acertos'].max()}")
    print(f"Pior pontuacao historica:    {df_materia['acertos'].min()}")
    
    if len(df_materia) > 1:
        ultima_nota = df_materia.iloc[-1]['nota_porcentagem']
        penultima_nota = df_materia.iloc[-2]['nota_porcentagem']
        variacao = ultima_nota - penultima_nota
        sinal = "+" if variacao >= 0 else ""
        print(f"Evolucao em relacao a ultima aula: {sinal}{variacao:.1f}% de rendimento.")
    print("=" * 70 + "\n")
    
    gerar_grafico_evolucao(materia_alvo, df_materia)

# --- SESSÃO PRINCIPAL DE ESTUDOS ---
def executar_cronometro():
    dados_historico = carregar_dados()
    
    print("="*45)
    print("      SISTEMA INTECOGNITSTE DE ESTUDOS       ")
    print("="*45)
    
    materia = input("Qual materia voce vai estudar agora? ").strip().capitalize()
    if not materia:
        materia = "Geral"
        
    # Mudança aqui: Entrada agora pede minutos inteiros para evitar confusão matemática
    tempo_alvo_minutos = obter_input_float("Quantos MINUTOS de estudo planeja cumprir hoje? (Ex: 60 ou 90): ", minimo=0.5)
    tempo_alvo_segundos = tempo_alvo_minutos * 60
    
    print("\n[INFO] PRONTO! Va para o DuckDuckGo, acesse a plataforma Metodo OBA e coloque a aula em TELA CHEIA.")
    print("[INFO] O cronometro so rodara se voce estiver na pagina correta e em tela cheia.")
    print("[INFO] Para encerrar a sessao a qualquer momento, pressione Ctrl+C aqui.")
    print("-" * 65)

    tempo_estudado = 0
    tempo_desperdiçado = 0
    distracoes_count = 0
    em_tela_cheia = False
    
    last_time = time.time()
    
    try:
        while tempo_estudado < tempo_alvo_segundos:
            time.sleep(0.5)
            agora = time.time()
            decorrido = agora - last_time
            last_time = agora
            
            status_atual_tela = verificar_tela_cheia()
            
            if status_atual_tela:
                if not em_tela_cheia:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [FOCO] Aula da Mentoria detectada! Cronometro rodando.")
                    em_tela_cheia = True
                tempo_estudado += decorrido
            else:
                if em_tela_cheia:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [DESVIO] Voce saiu da aula ou mudou de aba! Computando desvio...")
                    distracoes_count += 1
                    em_tela_cheia = False
                tempo_desperdiçado += decorrido
            
            min_foco, seg_foco = divmod(int(tempo_estudado), 60)
            min_perda, seg_perda = divmod(int(tempo_desperdiçado), 60)
            print(f"\rFoco: {min_foco:02d}m{seg_foco:02d}s | Desvios: {distracoes_count} ({min_perda:02d}m{seg_perda:02d}s perdidos) | Progresso: {(tempo_estudado/tempo_alvo_segundos)*100:.1f}%", end="")

    except KeyboardInterrupt:
        print("\n\n[AVISO] Sessao finalizada pelo usuario.")
    
    print("\n\n" + "===" * 5 + " SESSAO CONCLUIDA " + "===" * 5)
    finalizar = input("Quer prosseguir para o simulado do NotebookLM? (s/n): ").strip().lower()
    
    if finalizar == 's':
        prompt_notebook_lm = (
            f"Atue como um Professor especialista na materia de '{materia}'. "
            f"Com base exclusivamente nos documentos que importei no meu NotebookLM, "
            f"gere um simulado rigoroso de exatamente 10 questoes ineditas de multipla escolha (A a D) "
            f"para testar meu nivel de retencao de conteudo. Nao de as respostas imediatamente, coloque o gabarito "
            f"comentado apenas no final para eu nao ver antes de responder."
        )
        
        pyperclip.copy(prompt_notebook_lm)
        
        print("\n" + "="*60)
        print("[SUCESSO] PROMPT COPIADO COM SUCESSO PARA SEU CTRL+V!")
        print("="*60)
        print("Proximos passos:\n1. Abra o seu NotebookLM.\n2. De Ctrl+V no chat e envie.\n3. Responda as 10 questoes la.")
        print("4. Quando terminar, volte aqui para registrar seus acertos.\n")
        
        print("-" * 40)
        acertos = obter_input_int("Quantas questoes voce ACERTOU (0 a 10)? ", 0, 10)
        erros = 10 - acertos
        print(f"[INFO] Registrado: {acertos} Acertos e {erros} Erros.")
        
        sessao_atual = {
            "data": datetime.now().strftime("%Y-%m-%d"),
            "materia": materia,
            "tempo_alvo_s": round(tempo_alvo_segundos, 1),
            "tempo_estudado_s": round(tempo_estudado, 1),
            "tempo_perdido_s": round(tempo_desperdiçado, 1),
            "distracoes": distracoes_count,
            "acertos": acertos,
            "erros": erros,
            "nota_porcentagem": (acertos / 10) * 100
        }
        
        dados_historico.append(sessao_atual)
        salvar_dados(dados_historico)
        print("\n[SUCESSO] Dados salvos com sucesso!")
        
        exibir_dashboard(materia)
    else:
        print("\n[AVISO] Sessao encerrada sem salvar os dados.")

if __name__ == "__main__":
    executar_cronometro()