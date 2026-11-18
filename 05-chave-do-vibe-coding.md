---
id: 05-chave-do-vibe-coding
title: Missão 5 — A Chave do Vibe Coding
start: CASA-656
pickup: PRACA-029
pickup_objective: Pegue a Chave Mestra em [PRACA-029]
target: CASA-353
objective: Leve a Chave Mestra até Lucia em [CASA-353]
give_item: chave-secreta
require_item: chave-secreta
delivery_prompt: Lucia está com a Caixa Secreta em [CASA-353]. Entregue a Chave Mestra para abri-la:
wrong_item_message: Essa chave não gira nem parafuso! Cadê a Chave Mestra?
---

## CUTSCENE_INICIO
left: guanabara
right: lucia
bg: Sudeste da cidade em CASA-656

- Lucia: Guanabara, o Jason e eu já preparamos toda a bancada aqui em [CASA-353]! Só falta a Chave Mestra que o Sam Maltmon mencionou!
- Guanabara: Tô saindo do Sudeste agora mesmo! A [PRACA-029] fica logo ali na esquina.
- Lucia: Pega a chave e vem pro Centro! Toda a equipe está curiosa para saber o que tem dentro da Caixa Secreta!

## CUTSCENE_FIM
left: none
right: none
bg: splash/splash-end.png

- ENTREGAR: chave-secreta
- Narrador: A Chave Mestra gira na fechadura dourada da Caixa Secreta... e um brilho toma conta de todo o estúdio em [CASA-353]!
- Guanabara: Olá, Pequeno Gafanhoto! Dentro da caixa está o grande anúncio oficial: o Curso em Vídeo vai lançar o novo Curso de Vibe Coding!
- Guanabara: Um curso feito para a nova geração de programadores que estão chegando no mercado, unindo lógica, base sólida e Inteligência Artificial!
- Guanabara: Aguardamos todos vocês lá! Fiquem de olho nas redes sociais @gustavoguanabara e @cursoemvideo para saber a data de lançamento!
- Narrador: Missão cumprida! Agora você está livre para explorar a cidade ou revisitar qualquer missão pelo menu de pausa.
