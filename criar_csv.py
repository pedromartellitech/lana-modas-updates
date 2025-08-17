import pandas as pd
import os

# Caminho base do seu projeto
base_dir = r"C:\Users\pedro\OneDrive\Documentos\Venda"
data_dir = os.path.join(base_dir, "data")
os.makedirs(data_dir, exist_ok=True)

# Criar CSV de Vendas
cols_vendas = ["Data", "Produto", "Pagamento", "Valor", "Desconto(%)", "Valor Final"]
pd.DataFrame(columns=cols_vendas).to_csv(
    os.path.join(data_dir, "registros.csv"), index=False, encoding="utf-8"
)

# Criar CSV de Despesas
cols_despesas = ["Data", "Categoria", "Descricao", "Valor"]
pd.DataFrame(columns=cols_despesas).to_csv(
    os.path.join(data_dir, "despesas.csv"), index=False, encoding="utf-8"
)

print(f"✅ Arquivos criados em: {data_dir}")
