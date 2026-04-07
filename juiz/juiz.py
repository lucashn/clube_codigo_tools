import sys
import os
import subprocess

def main():
    # Verifica se os argumentos foram passados corretamente
    if len(sys.argv) != 3:
        print("Uso: python juiz.py <pasta_do_problema> <arquivo_codigo.py>")
        sys.exit(1)

    pasta_problema = sys.argv[1]
    codigo_py = sys.argv[2]

    pasta_entradas = os.path.join(pasta_problema, 'entradas')
    pasta_saidas = os.path.join(pasta_problema, 'saidas')

    # Valida a existência das pastas
    if not os.path.exists(pasta_entradas) or not os.path.exists(pasta_saidas):
        print("Erro: As pastas 'entradas' e/ou 'saidas' não foram encontradas dentro da pasta do problema.")
        sys.exit(1)

    # Valida a existência do arquivo de código
    if not os.path.exists(codigo_py):
        print("Erro: O arquivo de código especificado não existe")
        sys.exit(1)

    # Busca todos os arquivos .in na pasta de entradas
    arquivos_entrada = [f for f in os.listdir(pasta_entradas) if f.endswith('.in')]
    if not arquivos_entrada:
        print("Erro: Nenhum arquivo de entrada (.in) encontrado.")
        sys.exit(1)

    testes_falhos = []
    total_testes = len(arquivos_entrada)

    # Ordena os arquivos para testar na ordem correta (1.in, 2.in...)
    # Usando key para ordenar numericamente se o padrão for numérico
    try:
        arquivos_entrada.sort(key=lambda x: int(x.split('.')[0]))
    except ValueError:
        arquivos_entrada.sort()

    for arq_in in arquivos_entrada:
        nome_base = arq_in.replace('.in', '')
        arq_sol = f"{nome_base}.sol"
        
        caminho_in = os.path.join(pasta_entradas, arq_in)
        caminho_sol = os.path.join(pasta_saidas, arq_sol)

        if not os.path.exists(caminho_sol):
            print(f"Aviso: Arquivo de saída esperado '{arq_sol}' não encontrado. Pulando teste {nome_base}.")
            total_testes -= 1
            continue

        # Lê o conteúdo da entrada e a saída esperada
        with open(caminho_in, 'r', encoding='utf-8') as f_in:
            entrada_conteudo = f_in.read()
            
        with open(caminho_sol, 'r', encoding='utf-8') as f_sol:
            # strip() remove espaços em branco e quebras de linha no final do arquivo,
            # o que evita falhas bobas por conta de uma linha em branco extra.
            saida_esperada = f_sol.read().strip()

        # Executa o código do usuário isoladamente
        try:
            resultado = subprocess.run(
                [sys.executable, codigo_py],
                input=entrada_conteudo,
                text=True,
                capture_output=True,
                timeout=5 # Limite de tempo de 5 segundos
            )
            
            saida_obtida = resultado.stdout.strip()
            erros_execucao = resultado.stderr.strip()

            # Verifica se houve erro (crash) durante a execução
            if resultado.returncode != 0:
                testes_falhos.append({
                    'teste': nome_base,
                    'erro': f"Erro de Execução (Return Code {resultado.returncode}):\n{erros_execucao}"
                })
            # Verifica se a saída está correta (Wrong Answer)
            elif saida_obtida != saida_esperada:
                testes_falhos.append({
                    'teste': nome_base,
                    'esperado': saida_esperada,
                    'obtido': saida_obtida
                })

        except subprocess.TimeoutExpired:
             testes_falhos.append({
                 'teste': nome_base,
                 'erro': "Tempo limite excedido (Time Limit Exceeded - TLE)."
             })
        except Exception as e:
            testes_falhos.append({
                 'teste': nome_base,
                 'erro': f"Erro interno ao rodar o script: {e}"
             })

    # Relatório de resultados
    print(f"\n--- Resultado da Avaliação ({codigo_py}) ---")
    if total_testes == 0:
        print("Nenhum teste foi executado.")
    elif not testes_falhos:
        print(f"✅ Correto! O programa passou em todos os {total_testes} casos de teste.")
    else:
        print(f"❌ Incorreto. Falhou em {len(testes_falhos)} de {total_testes} testes.\n")
        for falha in testes_falhos:
            print(f"--- Caso de Teste {falha['teste']} ---")
            if 'erro' in falha:
                print(falha['erro'])
            else:
                print(f"Saída Obtida:\n{falha['obtido']}\n")
                print(f"Saída Esperada:\n{falha['esperado']}")
            print("-" * 30)

if __name__ == "__main__":
    main()