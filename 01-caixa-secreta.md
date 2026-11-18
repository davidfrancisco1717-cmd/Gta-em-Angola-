---
id: 01-caixa-secreta
title: Missão 1 — A Caixa Secreta
start: CASA-001
pickup: PRACA-001
pickup_objective: Pegue a Caixa Secreta em [PRACA-001]
target: COM-320
objective: Leve a Caixa Secreta para Lucia em [COM-320]
give_item: caixa-secreta
require_item: caixa-secreta
delivery_prompt: Lucia quer guardar a Caixa Secreta em segurança em [COM-320]. Selecione o item:
wrong_item_message: Isso não é a Caixa Secreta! Olha direito!
---

## CUTSCENE_INICIO
left: guanabara
right: jason
bg: Frente da CASA-001

- Guanabara: Olá, Pequeno Gafanhoto! Bom dia, Jason! Já tomou aquele café para aguentar o código de hoje?
- Jason: Guanabara, esquece o café e olha o tamanho da encrenca! Deixaram uma caixa metálica trancada ali na [PRACA-001] com um adesivo escrito "Futuro do Curso em Vídeo".
- Guanabara: Uma caixa misteriosa? Será que é mais um monitor ultrawide ou alguém tentou mandar um ZIP sem senha?
- OPCAO: Vou lá buscar agora antes que vire repositório abandonado! -> NEXT
- OPCAO: Se tiver bug dentro, a gente resolve no Vibe Coding! -> NEXT
- OPCAO: Só espero que não seja uma caixa cheia de cabos VGA! -> NEXT
- Jason: Haha! Pega a caixa na [PRACA-001] e leva direto para a Lucia dentro de [COM-320], lá no Centro. Ela já preparou a bancada!

## CUTSCENE_FIM
left: guanabara
right: lucia
bg: Interior do COM-320

- Lucia: Chegou bem na hora, Guanabara! Trouxe a famosa Caixa Secreta sem bater em nenhum poste?
- Guanabara: Quase nenhum! Olha ela aqui, intacta e pesada igual projeto com mil dependências no node_modules:
- ENTREGAR: caixa-secreta
- Lucia: Hmm... trancada a sete chaves! E só tem uma fechadura dourada bem no meio.
- Guanabara: E agora? Vamos pedir para uma IA adivinhar a senha?
- Lucia: Nem pensar, vai que ela alucina um número de 40 dígitos! Vou deixar a caixa guardada aqui no estúdio. Enquanto isso, corre porque o Jason está precisando de uma ajuda urgente com a placa de vídeo!
