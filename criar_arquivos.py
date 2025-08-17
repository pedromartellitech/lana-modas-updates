import pandas as pd

# Criar arquivo de vendas
df_vendas = pd.DataFrame(columns=["Data", "Cliente", "Telefone", "Produto", "Pagamento", "Valor"])
df_vendas.to_csv("registros.csv", index=False)
print("✅ Arquivo registros.csv criado com sucesso.")

# Criar arquivo de despesas
df_despesas = pd.DataFrame(columns=["Data", "Categoria", "Descricao", "Valor"])
df_despesas.to_csv("despesas.csv", index=False)
print("✅ Arquivo despesas.csv criado com sucesso.")
