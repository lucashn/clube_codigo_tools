"""
Reorganiza os arquivos de gabarito para o formato entendido pelo juiz.
"""

import sys
import shutil
from pathlib import Path

def reorganizar_casos_de_teste(pasta_raiz, pasta_destino):
    raiz = Path(pasta_raiz)
    destino = Path(pasta_destino)

    pasta_entradas = destino / "entradas"
    pasta_saidas = destino / "saidas"

    pasta_entradas.mkdir(parents=True, exist_ok=True)
    pasta_saidas.mkdir(parents=True, exist_ok=True)

    pastas_conjuntos = []
    for item in raiz.iterdir():
        if item.is_dir() and item.name.isdigit():
            pastas_conjuntos.append(int(item.name))
    
    pastas_conjuntos.sort()

    novo_numero_teste = 1

    for conjunto in pastas_conjuntos:
        caminho_conjunto = raiz / str(conjunto)
        
        testes_in = []
        for arquivo in caminho_conjunto.glob("*.in"):
            if arquivo.stem.isdigit():
                testes_in.append(int(arquivo.stem))
        
        testes_in.sort()

        for numero_teste in testes_in:
            arquivo_in = caminho_conjunto / f"{numero_teste}.in"
            arquivo_sol = caminho_conjunto / f"{numero_teste}.sol"

            if arquivo_in.exists() and arquivo_sol.exists():
                novo_arquivo_in = pasta_entradas / f"{novo_numero_teste}.in"
                novo_arquivo_sol = pasta_saidas / f"{novo_numero_teste}.sol"

                # Copia preservando metadados
                shutil.copy2(arquivo_in, novo_arquivo_in)
                shutil.copy2(arquivo_sol, novo_arquivo_sol)

                print(f"Copiado: Conjunto {conjunto}, Teste {numero_teste} ->")
                print(f"  -> {novo_arquivo_in.relative_to(destino)}")
                print(f"  -> {novo_arquivo_sol.relative_to(destino)}")
                
                novo_numero_teste += 1
            else:
                print(f"Aviso: Par incompleto no Conjunto {conjunto}, Teste {numero_teste}. Ignorando.")

    print(f"\nFinalizado! {novo_numero_teste - 1} pares de teste reorganizados.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso correto: python reorganizar_gabarito.py <pasta_raiz> <pasta_destino>")
        sys.exit(1)
    
    raiz_arg = sys.argv[1]
    destino_arg = sys.argv[2]
    
    if not Path(raiz_arg).exists():
        print(f"Erro: A pasta raiz '{raiz_arg}' não foi encontrada.")
        sys.exit(1)

    reorganizar_casos_de_teste(raiz_arg, destino_arg)