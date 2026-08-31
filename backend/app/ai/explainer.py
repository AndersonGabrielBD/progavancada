"""Camada de IA que converte a decisão estruturada do motor de otimização em uma
justificativa em linguagem natural (seção 9 do desafio).

Se ANTHROPIC_API_KEY estiver configurada, usa a API da Anthropic (Claude) para gerar
o texto. Caso contrário (ambiente offline, CI, demo sem chave), cai em um gerador
determinístico baseado em template — o sistema nunca fica sem explicação, apenas
com uma explicação mais simples. Isso mantém os testes automatizados determinísticos
mesmo sem acesso à rede.
"""
import os


def _template_explanation(ctx: dict) -> str:
    ok_recursos = "sim" if ctx.get("resources_ok") else "não"
    ok_acessibilidade = "sim" if ctx.get("accessibility_ok") else "não (não exigida)"
    if not ctx.get("accessibility_required"):
        ok_acessibilidade = "não exigida"
    elif ctx.get("accessibility_ok"):
        ok_acessibilidade = "sim"
    else:
        ok_acessibilidade = "não"

    return (
        f"Sala {ctx['room_code']} recomendada para {ctx['team_name']}. "
        f"Capacidade da sala: {ctx['capacity']} pessoas. Equipe: {ctx['team_size']} pessoas. "
        f"Ocupação prevista: {ctx['occupancy_pct']}%. "
        f"Recursos necessários atendidos: {ok_recursos}. "
        f"Acessibilidade: {ok_acessibilidade}. "
        f"Alternativas avaliadas: {ctx['alternatives_evaluated']}. "
        "Esta sala apresentou o melhor equilíbrio entre capacidade, localização e "
        "restrições dentre as alternativas disponíveis nesta execução."
    )


def _anthropic_explanation(ctx: dict) -> str | None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        prompt = (
            "Explique em 1 parágrafo curto, em português, por que a sala foi recomendada "
            "para a equipe, com base nestes dados estruturados. Seja objetivo e cite os "
            f"números. Dados: {ctx}"
        )
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=220,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except Exception:
        # Qualquer falha na chamada de IA (rede, cota, etc.) não pode derrubar o
        # motor de alocação — cai para o template determinístico.
        return None


def generate_explanation(ctx: dict) -> str:
    text = _anthropic_explanation(ctx)
    if text:
        return text
    return _template_explanation(ctx)
