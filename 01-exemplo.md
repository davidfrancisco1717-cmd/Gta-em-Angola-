---
id: 01-exemplo
title: Missão 1 — Missão Modelo
start: CASA-001
pickup: PRACA-001
pickup_objective: Pegue [ITEM-item-chave] em [PRACA-001]
target: COM-001
objective: Entregue [ITEM-item-chave] para [Contato] em [COM-001]
give_item: item-chave
require_item: item-chave
delivery_prompt: Aqui vai o pedido de entrega de [ITEM-item-chave] para [Contato] em [COM-001]:
wrong_item_message: Esse não é o [ITEM-item-chave]! Tente novamente.
---

## CUTSCENE_INICIO
left: protagonista
right: contato
bg: Frente da CASA-001

- Protagonista: Aqui vai a fala inicial do personagem principal com **negrito**, *itálico* e __sublinhado__.
- Contato: Aqui vai a resposta de [Contato] pedindo para ir até [PRACA-001] e depois para [COM-001].
- LINK: Abrir link de exemplo -> https://example.com
- OPCAO: Aqui vai uma opção que avança a missão -> NEXT
- OPCAO: Aqui vai uma opção que causa derrota -> FAIL: Exemplo de derrota por escolha na cutscene.
- Contato: Ótimo! Pegue [ITEM-item-chave] em [PRACA-001] e leve até [COM-001].

## CUTSCENE_FIM
left: protagonista
right: contato
bg: Interior do COM-001

- Contato: Aqui vai a fala final de [Contato] recebendo o item em [COM-001].
- ENTREGAR: item-chave
- Protagonista: Aqui vai a fala de encerramento da missão!
