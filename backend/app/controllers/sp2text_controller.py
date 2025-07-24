from app.models.speech2text import transcribe_from_microphone

async def spech_2_text():
    result = transcribe_from_microphone()
    print(result)
    return result