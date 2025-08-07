"""
Script de inicialização automática para popular a tabela profit
Este script é executado automaticamente quando a aplicação sobe
"""

import os
from .populate_profit_data import populate_profit_if_empty

def auto_populate_profit_data(cur, conn):
    """
    Popula automaticamente a tabela profit se ela estiver vazia
    """
    # Verificar se deve fazer população automática (via variável de ambiente)
    auto_populate = os.getenv("AUTO_POPULATE_PROFIT", "true").lower() == "true"
    
    if not auto_populate:
        print("⏭️  População automática desabilitada (AUTO_POPULATE_PROFIT=false)")
        return
    
    try:
        # Gerar dados dos últimos 24 meses (configurável via env)
        months_back = int(os.getenv("PROFIT_MONTHS_BACK", "24"))
        
        # Usar a função otimizada que já verifica se a tabela está vazia
        populate_profit_if_empty(cur, conn, months_back)
        
    except Exception as e:
        print(f"❌ Erro durante população automática: {e}")
        print("⚠️  A aplicação continuará sem os dados iniciais")
