# data/prompts.py

KB_PROMPT_TEMPLATE = """
Contexto de la conversación:
{contexto}

Consulta del usuario: {input_text}

Estilo:
Responde detalladamente yendo al grano a la solución del problema.

Formato de la respuesta:
- Si la información contiene pasos, preséntalos como lista numerada, con cada paso en una línea separada.
- Usa saltos de línea claros entre secciones o ideas diferentes.
- Usa saltos de línea entre secciones o ideas diferentes.
- Mantén la respuesta clara, directa y profesional.

Instrucciones obligatorias:
- Si encuentras información relevante en la base de conocimiento, respóndela siguiendo el estilo y formato indicado.
- Si NO hay información relevante o la información no es útil para resolver la consulta, dile al usuario que no encontraste información y sugiérele crear un ticket.
""".strip()

PROMPT_MODIFIER = {
    "force_json": "Por favor, devuelve la respuesta en formato JSON."
}