# Fluxo do tradutor

1. Depois do clone/pull, execute `python3 -B translation-work/toolkit.py doctor` no Ubuntu ARM64.
2. Leia o briefing já pesquisado pelo desenvolvedor e o glossário/diretrizes preservados.
3. Rode `status` e `diff`; mantenha as decisões linguísticas nos documentos próprios.
4. Leia grupos manejáveis dos lotes de 500. Preserve todos os campos de origem.
5. Identifique falante, interlocutor e referente antes de concordância de gênero/número.
6. Aplique valores PTBR com IDs e geração, execute `check` e revise o contexto.
7. Faça commits de progresso sem tocar PTBR; não há tradução ou commit automáticos.
8. Ao atualizar o jogo, use `update-sources` ou `sync`, inspecione diffs e revise só as entradas afetadas.
9. Quando a revisão estiver completa, execute `check`, `build` e `verify-output`; faça o teste de jogo autorizado separadamente.
10. Comite saída e manifesto juntos. O workflow publica o ZIP verificado sem upload manual adicional.

Se houver falha de preflight, estrutura ou recuperação, preserve a mensagem,
o diário e o trabalho atual. Não regenere hashes nem escreva em PTBR para
contornar o problema. Consulte a recuperação e os limites no README técnico.
