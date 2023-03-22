import os
import time
import nltk
from azure.cognitiveservices import speech as speechsdk
from twitchio.ext import commands
from chat import *

output_file_name_with_path = '{0}\\output.wav'.format(os.path.dirname(__file__))


def get_value_from_json_key(key_name):
    with open("config.json", "r") as file:
        json_data = json.load(file)
    for i in json_data:
        if str(i) == str(key_name):
            return str(json_data[i])


def get_audio_or_return_error(result):
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        stream = speechsdk.AudioDataStream(result)
        stream.save_to_wav_file(output_file_name_with_path)
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                print("Error details: {}".format(cancellation_details.error_details))
                print("Did you set the speech resource key and region values?")


def get_output_audio_file(text):
    # This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
    speech_config = speechsdk.SpeechConfig(subscription=get_value_from_json_key("microsoft-azure-api-key"),
                                           region=get_value_from_json_key("microsoft-azure-speech-region"))
    speech_config.speech_synthesis_voice_name = get_value_from_json_key("voice-name")
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
    # The language of the voice that speaks.
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    # Get text from the console and synthesize to the default speaker.
    print("<Speaking...>")
    with open("output.txt", "a", encoding="utf-8") as out:
        out.write(str(text) + "\n")
    speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()
    get_audio_or_return_error(speech_synthesis_result)


def generate_conversation(message_content, message_author):
    print('------------------------------------------------------')
    print(message_content)
    print(message_author)
    print(Bot.conversation)

    Bot.conversation.append(f'CHATTER: {message_content}')
    text_block = '\n'.join(Bot.conversation)
    prompt = open_file('prompt_chat.txt').replace('<<BLOCK>>', text_block)
    bot_name = get_value_from_json_key("bot-name")
    prompt = prompt + '\n' + bot_name + ':'
    print(prompt)
    response = gpt3_completion(prompt)
    print(bot_name + ': ', response)
    if Bot.conversation.count(bot_name + ': ' + response) == 0:
        Bot.conversation.append(bot_name + f': {response}')
    return response


def generate_ssml(response):
    ssml_text = '<speak>'
    response_counter = 0
    mark_array = []
    for s in response.split(' '):
        ssml_text += f'<bookmark mark="{response_counter}"/>{s}'
        mark_array.append(s)
        response_counter += 1
    ssml_text += '</speak>'
    return ssml_text


def get_audio_and_text(message_content, message_author):
    response = generate_conversation(message_content, message_author)
    response = message_content + "? " + response
    generate_ssml(response)
    get_output_audio_file(str(response))
    audio_file = output_file_name_with_path
    time.sleep(2)
    open('output.txt', 'w').close()
    print('------------------------------------------------------')
    os.remove(audio_file)


class Bot(commands.Bot):
    conversation = list()

    def __init__(self):
        # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        # prefix can be a callable, which returns a list of strings or a string...
        # initial_channels can also be a callable which returns a list of strings...
        super().__init__(token=get_value_from_json_key("twitch-access-key"), prefix='!',
                         initial_channels=[get_value_from_json_key("twitch-account-name")])

    async def event_ready(self):
        # Notify us when everything is ready!
        # We are logged in and ready to chat and use commands...
        print(f'Logged in as | {self.nick}')

    async def event_message(self, message):
        # Messages with echo set to True are messages sent by the bot...
        # For now, we just want to ignore them...
        if not message.echo:
            # download the words corpus
            nltk.download('words')
            # Check if the message contains english words
            if any(word in message.content for word in nltk.corpus.words.words()):
                # Check if the message is too long
                if len(message.content) <= 70:
                    get_audio_and_text(message.content, message.author.name)
                    # Since we have commands and are overriding the default `event_message`
                    # We must let the bot know we want to handle and invoke our commands...
        await self.handle_commands(message)

    @commands.command()
    async def hello(self, ctx: commands.Context):
        # Here we have a command hello, we can invoke our command with our prefix and command name
        # e.g ?hello
        # We can also give our commands aliases (different names) to invoke with.

        # Send a hello back!
        # Sending a reply back to the channel is easy... Below is an example.
        await ctx.send(f'Hello {ctx.author.name}!')


bot = Bot()
bot.run()
# bot.run() is blocking and will stop execution of any below code here until stopped or closed.
