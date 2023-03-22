import json
import openai


def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()


def get_value_from_json_key(key_name):
    with open("config.json", "r") as file:
        json_data = json.load(file)
    for i in json_data:
        if str(i) == str(key_name):
            return json_data[i]


openai.api_key = get_value_from_json_key("openapi-key")


def gpt3_completion(prompt, engine='text-davinci-003', temp=0.5, tokens=75, freq_pen=2.0, pres_pen=2.0,
                    stop=None):
    if stop is None:
        stop = [get_value_from_json_key("bot-name") + ':', 'CHATTER:']
    prompt = prompt.encode(encoding='ASCII', errors='ignore').decode()
    response = openai.Completion.create(
        engine=engine,
        prompt=prompt,
        temperature=temp,
        max_tokens=tokens,
        frequency_penalty=freq_pen,
        presence_penalty=pres_pen,
        stop=stop)
    text = response['choices'][0]['text'].strip()
    return text
