# Reis Barber

## Executar o backend

1. Instale o Python 3 no computador.
2. Abra o terminal nesta pasta.
3. Execute:

```powershell
python server.py
```

4. Abra `http://127.0.0.1:8000` no navegador.

O backend cria `data.json` automaticamente e oferece:

- `POST /api/login`: login do barbeiro.
- `GET /api/appointments`: horários públicos reservados, sem dados pessoais.
- `POST /api/appointments`: cria um agendamento.
- `GET /api/barber/appointments`: agenda completa protegida.
- `DELETE /api/barber/appointments/{id}`: cancela um agendamento.

Usuário inicial: `Al3xandre`
Senha inicial: `Reis19223!`

A senha deve ser alterada antes de publicar o sistema na internet. Para produção, use HTTPS, banco de dados e variáveis de ambiente para o segredo.
