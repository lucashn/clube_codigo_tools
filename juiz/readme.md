# juiz

Realiza a correção automática de um código em Python utilizando como base pares de arquivos de entrada e saída.
Ao final da correção, o resultado final e o número de testes corretos e incorretos será mostrado.
Existe um tempo limite fixo de 5 segundos para cada execução do programa.

## Formato de um problema

Cada problema deve estar contido em uma pasta. A pasta deverá conter as subpastas 'entradas' (contendo arquivos 1.in, 2.in, 3.in, etc) e 'saidas'
(contendo arquivos 1.sol, 2.sol, 3.sol e etc).

## Forma de uso

  $ python juiz.py {pasta_problema} {codigo.py}

## Exemplo

  python juiz.py ./exemplo/pizzaria exemplo/pizzaria_correto.py