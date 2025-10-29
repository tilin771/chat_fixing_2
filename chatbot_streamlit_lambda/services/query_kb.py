from data.connections import bedrock_agent_client, MODEL_ARN, KB_ID
from data.prompts import KB_PROMPT_TEMPLATE


def consultar_kb_streaming(input_text, contexto, prioridad=7):
    metadata_filter = {"lessThanOrEquals": {"key": "Prioridad", "value": prioridad}}

    prompt = KB_PROMPT_TEMPLATE.format(contexto=contexto, input_text=input_text)

    response = bedrock_agent_client.retrieve_and_generate_stream(
        input={"text": prompt},
        retrieveAndGenerateConfiguration={
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": KB_ID,
                "modelArn": MODEL_ARN,
                "retrievalConfiguration": {
                    "vectorSearchConfiguration": {
                        "filter": metadata_filter,
                        "numberOfResults": 3
                    }
                }
            },
            "type": "KNOWLEDGE_BASE"
        }
    )

    for event in response['stream']:
        if 'output' in event and 'text' in event['output']:
            yield event['output']['text']
