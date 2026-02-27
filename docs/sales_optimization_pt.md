i# Demo de Otimização de ORM para Vendas

Este projeto demonstra a diferença entre um uso custoso do ORM e uma abordagem otimizada ao gerar relatórios CSV.

## Modelo de Domínio

- `Reseller` está ligado ao `User` do Django com `OneToOneField`.
- `Product` possui relação muitos-para-muitos com `Category`.
- `Sale` possui múltiplos registros de `SaleItem`.
- `SaleItem` guarda snapshot de `category`, `quantity`, `unit_price` e `line_total`.

## Carga de Dados (Seed)

Use o comando para criar um volume alto de dados:

```bash
python manage.py seed_sales
```

Volume padrão:

- 1.000 usuários/revendedores
- 80 categorias
- 10.000 produtos
- 100.000 vendas
- 2 a 4 itens por venda (~300.000 itens de venda em média)

Opções úteis:

```bash
python manage.py seed_sales --reset
python manage.py seed_sales --sale-count 200000 --chunk-size 8000
```

## APIs

### 1) Relatório CSV não otimizado

Endpoint:

- `GET /sales/reports/unoptimized`

Características:

- Faz leituras relacionais dentro de loops Python.
- Dispara N+1 queries de forma proposital.
- Monta e retorna o CSV inteiro em memória.
- É útil para demonstrar gargalos de performance.

### 2) Relatório CSV otimizado com streaming

Endpoint:

- `GET /sales/reports/optimized`

Características:

- Usa `select_related` e `prefetch_related` para reduzir queries extras.
- Usa `values_list` para buscar apenas as colunas necessárias.
- Faz streaming de linhas via `StreamingHttpResponse`.
- Reduz uso de memória em exports grandes.

## Por que isso importa

Em bases grandes, padrões de otimização no Django ORM impactam diretamente:

- Quantidade de queries
- Tempo de resposta
- Consumo de memória durante exportação

Este repositório foi estruturado para que ambas as implementações gerem o mesmo schema de CSV e possam ser comparadas lado a lado.

## Nota de Segurança de Dependência

- Use `djangorestframework` (pacote oficial).
- Evite `django-restframework` (nome parecido, estilo typosquatting).
- Confirme dependências instaladas com `uv pip list`.
