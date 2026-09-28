def test_pagina_inicial_retorna_html_com_titulo(cliente):
    resposta = cliente.get("/")

    assert resposta.status_code == 200
    assert resposta.headers["content-type"].startswith("text/html")
    assert "<title>Cadastro de produtos</title>" in resposta.text
    assert "<h1>Cadastro de produtos</h1>" in resposta.text
