def test_saude_ok_com_banco_disponivel(cliente):
    resposta = cliente.get("/health")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok", "banco": "ok"}


def test_saude_503_com_banco_indisponivel(cliente, ambiente):
    # Porta sem nenhum serviço escutando: a conexão falha de verdade.
    ambiente.setenv("POSTGRES_HOST", "127.0.0.1")
    ambiente.setenv("POSTGRES_PORT", "1")

    resposta = cliente.get("/health")

    assert resposta.status_code == 503
    assert resposta.json() == {"status": "erro", "banco": "indisponivel"}


def test_saude_503_com_configuracao_incompleta(cliente, ambiente):
    ambiente.delenv("POSTGRES_PASSWORD")

    resposta = cliente.get("/health")

    assert resposta.status_code == 503
    assert resposta.json() == {"status": "erro", "banco": "indisponivel"}
