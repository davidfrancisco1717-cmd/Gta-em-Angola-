---
id: 04-peca-do-robo
title: Missão 4 — Deploy na Sexta-Feira
start: COM-554
pickup: PRACA-025
pickup_objective: Pegue a Peça de Robô em [PRACA-025]
target: CASA-656
objective: Entregue a Peça de Robô para Sam Maltmon em [CASA-656]
give_item: peca-robo
require_item: peca-robo
delivery_prompt: Sam Maltmon precisa da Peça de Robô em [CASA-656]. Selecione o item correto:
wrong_item_message: Meus tokens não dão conta disso... cadê a Peça de Robô?
---

## CUTSCENE_INICIO
left: guanabara
right: maltmon
bg: Frente do COM-554

- Sam Maltmon: Guanabara, ainda bem que atendeu! Eu disse para o meu robô assistente: "só ajusta esse CSS rapidinho", e ele resolveu fazer deploy em produção na sexta-feira!
- Guanabara: Fazer deploy na sexta às seis da tarde? Até a IA deveria saber dessa regra sagrada!
- Sam Maltmon: Pois é, no susto ele perdeu o módulo neural ali na [PRACA-025]! Sem essa peça de robô ele fica só repetindo "Vou pensar passo a passo..." sem sair do lugar.
- Guanabara: Deixa comigo, Sam Maltmon! Pego a peça na [PRACA-025] e levo até você em [CASA-656], lá no Sudeste!

## CUTSCENE_FIM
left: guanabara
right: maltmon
bg: Interior da CASA-656

- Sam Maltmon: Rápido igual geração de código com zero latência! Trouxe a peça do meu robô?
- Guanabara: Trouxe inteirinha! E já avisa pra ele que sexta-feira é dia de backup, não de deploy. Toma aí:
- ENTREGAR: peca-robo
- Sam Maltmon: Excelente! Agora posso revelar o que o robô estava protegendo o tempo todo...
- Guanabara: Não me diga que era a chave daquela Caixa Secreta!
- Sam Maltmon: Exatamente! A Chave Mestra está na [PRACA-029], bem pertinho daqui. Pega ela e corre para encontrar a Lucia em [CASA-353], no Centro. Chegou a hora de abrir a caixa!
